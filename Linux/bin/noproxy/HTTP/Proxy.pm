package HTTP::Proxy;

use HTTP::Daemon;
use HTTP::Date qw(time2str);
use LWP::UserAgent;
use LWP::ConnCache;
use Fcntl ':flock';         # import LOCK_* constants
use IO::Select;
use Sys::Hostname;          # hostname()
use Carp;

use strict;
use vars qw( $VERSION $AUTOLOAD @METHODS
             @ISA @EXPORT @EXPORT_OK %EXPORT_TAGS );

require Exporter;
@ISA    = qw(Exporter);
@EXPORT = ();               # no export by default
@EXPORT_OK = qw( ERROR NONE    PROXY  STATUS PROCESS SOCKET HEADERS FILTERS
                 DATA  CONNECT ENGINE ALL );
%EXPORT_TAGS = ( log => [@EXPORT_OK] );    # only one tag

$VERSION = '0.23';

my $CRLF = "\015\012";                     # "\r\n" is not portable

# standard filters
use HTTP::Proxy::HeaderFilter::standard;

# constants used for logging
use constant ERROR   => -1;    # always log
use constant NONE    => 0;     # never log
use constant PROXY   => 1;     # proxy information
use constant STATUS  => 2;     # HTTP status
use constant PROCESS => 4;     # sub-process life (and death)
use constant SOCKET  => 8;     # low-level connections
use constant HEADERS => 16;    # HTTP headers
use constant FILTERS => 32;    # Messages from filters
use constant DATA    => 64;    # Data received by the filters
use constant CONNECT => 128;   # Data transmitted by the CONNECT method
use constant ENGINE  => 256;   # Internal information from the Engine
use constant ALL     => 511;   # All of the above

# modules that need those constants to be defined
use HTTP::Proxy::Engine;
use HTTP::Proxy::FilterStack;

# Methods we can forward
my %METHODS;

# HTTP (RFC 2616)
$METHODS{http} = [qw( CONNECT DELETE GET HEAD OPTIONS POST PUT TRACE )];

# WebDAV (RFC 2518)
$METHODS{webdav} = [
    @{ $METHODS{http} },
    qw( COPY LOCK MKCOL MOVE PROPFIND PROPPATCH UNLOCK )
];

# Delta-V (RFC 3253)
$METHODS{deltav} = [
    @{ $METHODS{webdav} },
    qw( BASELINE-CONTROL CHECKIN CHECKOUT LABEL MERGE MKACTIVITY
        MKWORKSPACE REPORT UNCHECKOUT UPDATE VERSION-CONTROL ),
];

# the whole method list
@METHODS = HTTP::Proxy->known_methods();

# useful regexes (from RFC 2616 BNF grammar)
my %RX;
$RX{token}  = qr/[-!#\$%&'*+.0-9A-Z^_`a-z|~]+/;
$RX{mime}   = qr($RX{token}/$RX{token});
$RX{method} = '(?:' . join ( '|', @METHODS ) . ')';
$RX{method} = qr/$RX{method}/;

sub new {
    my $class  = shift;
    my %params = @_;

    # some defaults
    my %defaults = (
        agent    => undef,
        chunk    => 4096,
        daemon   => undef,
        host     => 'localhost',
        logfh    => *STDERR,
        logmask  => NONE,
        max_connections => 0,
        max_keep_alive_requests => 10,
        port     => 8080,
        stash    => {},
        timeout  => 60,
#        via      => hostname() . " (HTTP::Proxy/$VERSION)",
        x_forwarded_for => 0,
    );

    # non modifiable defaults
    my $self = bless { conn => 0, loop => 1 }, $class;

    # support for deprecated stuff
    {
        my %convert = (
            maxchild => 'max_clients',
            maxconn  => 'max_connections',
            maxserve => 'max_keep_alive_requests',
        );
        while( my ($old, $new) = each %convert ) {
            if( exists $params{$old} ) {
               $params{$new} = delete $params{$old};
               carp "$old is deprecated, please use $new";
            }
        }
    }

    # get attributes
    $self->{$_} = exists $params{$_} ? delete( $params{$_} ) : $defaults{$_}
      for keys %defaults;

    # choose an engine with the remaining parameters
    $self->{engine} = HTTP::Proxy::Engine->new( %params, proxy => $self );
    $self->log( PROXY, "PROXY", "Selected engine " . ref $self->{engine} );

    return $self;
}

sub known_methods {
    my ( $class, @args ) = @_;

    @args = map { lc } @args ? @args : ( keys %METHODS );
    exists $METHODS{$_} || carp "Method group $_ doesn't exist"
        for @args;
    my %seen;
    return grep { !$seen{$_}++ } map { @{ $METHODS{$_} || [] } } @args;
}

sub timeout {
    my $self = shift;
    my $old  = $self->{timeout};
    if (@_) {
        $self->{timeout} = shift;
        $self->agent->timeout( $self->{timeout} ) if $self->agent;
    }
    return $old;
}

sub url {
    my $self = shift;
    if ( not defined $self->daemon ) {
        carp "HTTP daemon not started yet";
        return undef;
    }
    return $self->daemon->url;
}

# normal accessors
for my $attr ( qw(
    agent chunk daemon host logfh port request response hop_headers
    logmask via x_forwarded_for client_headers engine
    max_connections max_keep_alive_requests
    )
  )
{
    no strict 'refs';
    *{"HTTP::Proxy::$attr"} = sub {
        my $self = shift;
        my $old  = $self->{$attr};
        $self->{$attr} = shift if @_;
        return $old;
      }
}

# read-only accessors
for my $attr (qw( conn loop client_socket )) {
    no strict 'refs';
    *{"HTTP::Proxy::$attr"} = sub { $_[0]{$attr} }
}

sub max_clients { shift->engine->max_clients( @_ ) }

# deprecated methods are still supported
{
    my %convert = (
        maxchild => 'max_clients',
        maxconn  => 'max_connections',
        maxserve => 'max_keep_alive_requests',
    );
    while ( my ( $old, $new ) = each %convert ) {
        no strict 'refs';
        *$old = sub {
            carp "$old is deprecated, please use $new";
            goto \&$new;
        };
    }
}

sub stash {
    my $stash = shift->{stash};
    return $stash unless @_;
    return $stash->{ $_[0] } if @_ == 1;
    return $stash->{ $_[0] } = $_[1];
}

sub new_connection { ++$_[0]{conn} }

sub start {
    my $self = shift;

    $self->init;
    $SIG{INT} = $SIG{TERM} = sub { $self->{loop} = 0 };

    # the main loop
    my $engine = $self->engine;
    $engine->start if $engine->can('start');
    while( $self->loop ) {
        $engine->run;
        last if $self->max_connections && $self->conn >= $self->max_connections;
    }
    $engine->stop if $engine->can('stop');

    $self->log( STATUS, "STATUS",
        "Processed " . $self->conn . " connection(s)" );

    return $self->conn;
}

# semi-private init method
sub init {
    my $self = shift;

    # must be run only once
    return if $self->{_init}++;

    $self->_init_daemon if ( !defined $self->daemon );
    $self->_init_agent  if ( !defined $self->agent );

    # specific agent config
    $self->agent->requests_redirectable( [] );
    $self->agent->agent('');    # for TRACE support
    $self->agent->protocols_allowed( [qw( http https ftp gopher )] );

    # standard header filters
    $self->{headers}{request}  = HTTP::Proxy::FilterStack->new;
    $self->{headers}{response} = HTTP::Proxy::FilterStack->new;

    # the same standard filter is used to handle headers
    my $std = HTTP::Proxy::HeaderFilter::standard->new();
    $std->proxy( $self );
    $self->{headers}{request}->push(  [ sub { 1 }, $std ] );
    $self->{headers}{response}->push( [ sub { 1 }, $std ] );

    # standard body filters
    $self->{body}{request}  = HTTP::Proxy::FilterStack->new(1);
    $self->{body}{response} = HTTP::Proxy::FilterStack->new(1);

    return;
}

#
# private init methods
#

sub _init_daemon {
    my $self = shift;
    my %args = (
        LocalAddr => $self->host,
        LocalPort => $self->port,
        ReuseAddr => 1,
    );
    delete $args{LocalPort} unless $self->port;    # 0 means autoselect
    my $daemon = HTTP::Daemon->new(%args)
      or die "Cannot initialize proxy daemon: $!";
    $self->daemon($daemon);

    return $daemon;
}

sub _init_agent {
    my $self  = shift;
    my $agent = LWP::UserAgent->new(
        env_proxy  => 1,
        keep_alive => 2,
        parse_head => 0,
        timeout    => $self->timeout,
      )
      or die "Cannot initialize proxy agent: $!";
    $self->agent($agent);
    return $agent;
}

# This is the internal "loop" that lets the child process process the
# incoming connections.

sub serve_connections {
    my ( $self, $conn ) = @_;
    my $response;
    $self->{client_socket} = $conn;  # read-only
    $self->log( SOCKET, "SOCKET", "New connection from " . $conn->peerhost
                      . ":" . $conn->peerport );

    my ( $last, $served ) = ( 0, 0 );

    while ( $self->loop() ) {
        my $req;
        {
            local $SIG{INT} = local $SIG{TERM} = 'DEFAULT';
            $req = $conn->get_request();
        }

        $served++;
#HERE - THIS LOOKS LIKE A GOOD PLACE FOR OUR STUFF NOPEN
        # initialisation
        $self->request($req);
        $self->response(undef);

        # Got a request?
        unless ( defined $req ) {
            $self->log( ERROR, "ERROR",
                "Getting request failed: " . $conn->reason )
                if $conn->reason ne 'No more requests from this connection';
            return;
        }
        $self->log( STATUS, "REQUEST", $req->method . ' '
           . ( $req->method eq 'CONNECT' ? $req->uri->host_port : $req->uri ) );

        # can we forward this method?
        if ( !grep { $_ eq $req->method } @METHODS ) {
            $response = HTTP::Response->new( 501, 'Not Implemented' );
            $response->content_type( "text/plain" );
            $response->content(
                "Method " . $req->method . " is not supported by this proxy." );
            $self->response($response);
            goto SEND;
        }

        # transparent proxying support
        if( not defined $req->uri->scheme ) {
            if( my $host = $req->header('Host') ) {
                 $req->uri->scheme( 'http' );
                 $req->uri->host( $host );
            }
            else {
                $response = HTTP::Response->new( 400, 'Bad request' );
                $response->content_type( "text/plain" );
                $response->content("Can't do transparent proxying without a Host: header.");
                $self->response($response);
                goto SEND;
            }
        }

        # can we serve this protocol?
        if ( !$self->is_protocol_supported( my $s = $req->uri->scheme ) )
        {
            # should this be 400 Bad Request?
            $response = HTTP::Response->new( 501, 'Not Implemented' );
            $response->content_type( "text/plain" );
            $response->content("Scheme $s is not supported by this proxy.");
            $self->response($response);
            goto SEND;
        }

        # select the request filters
        $self->{$_}{request}->select_filters( $req ) for qw( headers body );

        # massage the request
        $self->{headers}{request}->filter( $req->headers, $req );

        # FIXME I don't know how to get the LWP::Protocol objet...
        # NOTE: the request is always received in one piece
        $self->{body}{request}->filter( $req->content_ref, $req, undef );
        $self->{body}{request}->eod;    # end of data
        $self->log( HEADERS, "REQUEST", $req->headers->as_string );

        # CONNECT method is a very special case
        if( ! defined $self->response and $req->method eq 'CONNECT' ) {
            $last = $self->_handle_CONNECT($served);
            return if $last;
        }

        # the header filters created a response,
        # we won't contact the origin server
        # FIXME should the response header and body be filtered?
        goto SEND if defined $self->response;

        # FIXME - don't forward requests to ourselves!

        # pop a response
        my ( $sent, $chunked ) = ( 0, 0 );
        $response = $self->agent->simple_request(
            $req,
            sub {
                my ( $data, $response, $proto ) = @_;

                # first time, filter the headers
                if ( !$sent ) { 
                    $sent++;
                    $self->response( $response );
                    
                    # select the response filters
                    $self->{$_}{response}->select_filters( $response )
                      for qw( headers body );

                    $self->{headers}{response}
                         ->filter( $response->headers, $response );
                    ( $last, $chunked ) =
                      $self->_send_response_headers( $served );
                }

                # filter and send the data
                $self->log( DATA, "DATA",
                    "got " . length($data) . " bytes of body data" );
                $self->{body}{response}->filter( \$data, $response, $proto );
                if ($chunked) {
                    printf $conn "%x$CRLF%s$CRLF", length($data), $data
                      if length($data);    # the filter may leave nothing
                }
                else { print $conn $data; }
            },
            $self->chunk
        );

        # remove the header added by LWP::UA before it sends the response back
        $response->remove_header('Client-Date');

        # do a last pass, in case there was something left in the buffers
        my $data = "";    # FIXME $protocol is undef here too
        $self->{body}{response}->filter_last( \$data, $response, undef );
        if ( length $data ) {
            if ($chunked) {
                printf $conn "%x$CRLF%s$CRLF", length($data), $data;
            }
            else { print $conn $data; }
        }

        # last chunk
        print $conn "0$CRLF$CRLF" if $chunked;    # no trailers either
        $self->response($response);

        # the callback is not called by LWP::UA->request
        # in some case (HEAD, error)
        if ( !$sent ) {
            $self->response($response);
            $self->{$_}{response}->select_filters( $response )
              for qw( headers body );
            $self->{headers}{response}
                 ->filter( $response->headers, $response );
        }

        # what about X-Died and X-Content-Range?
        if( my $died = $response->header('X-Died') ) {
            $self->log( ERROR, "ERROR", $died );
            $sent = 0;
            $response = HTTP::Response->new( 500, "Proxy filter error" );
            $response->content_type( "text/plain" );
            $response->content($died);
            $self->response($response);
        }

      SEND:

        $response = $self->response ;

        # responses that weren't filtered through callbacks
        # (empty body or error)
        # FIXME some error response headers might not be filtered
        if ( !$sent ) {
            $self->{$_}{response}->select_filters( $response )
              for qw( headers body );
            ($last, $chunked) = $self->_send_response_headers( $served );
            my $content = $response->content;
            if ($chunked) {
                printf $conn "%x$CRLF%s$CRLF", length($content), $content
                  if length($content);    # the filter may leave nothing
                print $conn "0$CRLF$CRLF";
            }
            else { print $conn $content; }
        }

        # FIXME ftp, gopher
        $conn->print( $response->content )
          if defined $req->uri->scheme
             and $req->uri->scheme =~ /^(?:ftp|gopher)$/
             and $response->is_success;

        $self->log( SOCKET, "SOCKET", "Connection closed by the proxy" ), last
          if $last || $served >= $self->max_keep_alive_requests;
    }
    $self->log( SOCKET, "SOCKET", "Connection closed by the client" )
      if !$last
      and $served < $self->max_keep_alive_requests;
    $self->log( PROCESS, "PROCESS", "Served $served requests" );
    $conn->close;
}

# INTERNAL METHOD
# send the response headers for the proxy
# expects $served  (number of requests served)
# returns $last and $chunked (last request served, chunked encoding)
sub _send_response_headers {
    my ( $self, $served ) = @_;
    my ( $last, $chunked ) = ( 0, 0 );
    my $conn = $self->client_socket;
    my $response = $self->response;

    # correct headers
    $response->remove_header("Content-Length")
      if $self->{body}{response}->will_modify();
#    $response->header( Server => "HTTP::Proxy/$VERSION" )
#      unless $response->header( 'Server' );
    $response->header( Date => time2str(time) )
      unless $response->header( 'Date' );

    # this is adapted from HTTP::Daemon
    if ( $conn->antique_client ) { $last++ }
    else {
        my $code = $response->code;
        $conn->send_status_line( $code, $response->message,
            $self->request()->protocol() );
        if ( $code =~ /^(1\d\d|[23]04)$/ ) {

            # make sure content is empty
            $response->remove_header("Content-Length");
            $response->content('');
        }
        elsif ( $response->request && $response->request->method eq "HEAD" )
        {    # probably OK, says HTTP::Daemon
        }
        else {
            if ( $conn->proto_ge("HTTP/1.1") ) {
                $chunked++;
                $response->push_header( "Transfer-Encoding" => "chunked" );
                $response->push_header( "Connection"        => "close" )
                  if $served >= $self->max_keep_alive_requests;
            }
            else {
                $last++;
                $conn->force_last_request;
            }
        }
        print $conn $response->headers_as_string($CRLF);
        print $conn $CRLF;    # separates headers and content
    }
    $self->log( STATUS,  "RESPONSE", $response->status_line );
    $self->log( HEADERS, "RESPONSE", $response->headers->as_string );
    return ($last, $chunked);
}

# INTERNAL method
# FIXME no man-in-the-middle for now
sub _handle_CONNECT {
    my ($self, $served) = @_;
    my $last = 0;

    my $conn = $self->client_socket;
    my $req  = $self->request;
	#PRY NEED TO PUT THE NOPEN STUFF HERE (Create the appropriate tunnel and Modify the port/IP)
    my $upstream = IO::Socket::INET->new( PeerAddr => $req->uri->host_port );
    unless( $upstream and $upstream->connected ) {
        # 502 Bad Gateway / 504 Gateway Timeout
        # Note to implementors: some deployed proxies are known to
        # return 400 or 500 when DNS lookups time out.
        my $response = HTTP::Response->new( 200 );
        $response->content_type( "text/plain" );
        $self->response($response);
        return $last;
    }

    # send the response headers (FIXME more headers required?)
    my $response = HTTP::Response->new(200);
    $self->response($response);
    $self->{$_}{response}->select_filters( $response ) for qw( headers body );

    $self->_send_response_headers( $served );

    # we now have a TCP connection
    $last = 1;

    my $select = IO::Select->new;
    for ( $conn, $upstream ) {
         $_->autoflush(1);
         $_->blocking(0);
         $select->add($_);
    }

    # loop while there is data
    while ( my @ready = $select->can_read ) {
        for (@ready) {
            my $data = "";
            my ($sock, $peer, $from ) = $conn eq $_
                                      ? ( $conn, $upstream, "client" )
                                      : ( $upstream, $conn, "server" );

            # read the data
            my $read = $sock->sysread( $data, 4096 );
          
            # check for errors
            if(not defined $read ) {
                $self->log( ERROR, "CONNECT", "Read undef from $from ($!)" );
                next;
            }

            # end of connection
            if ( $read == 0 ) {
                $_->close for ( $sock, $peer );
                $select->remove( $sock, $peer );
                $self->log( SOCKET, "CONNECT", "Connection closed by the $from" );
                $self->log( PROCESS, "PROCESS", "Served $served requests" );
                next;
            }

            # proxy the data
            $self->log( CONNECT, "CONNECT", "$read bytes received from $from" );
            $peer->syswrite($data, length $data);
        }
    }
    $self->log( CONNECT, "CONNECT", "End of CONNECT proxyfication");
    return $last;
}

sub push_filter {
    my $self = shift;
    my %arg  = (
        mime   => 'text/*',
        method => join( ',', @METHODS ),
        scheme => 'http',
        host   => '',
        path   => '',
        query  => '',
    );

    # parse parameters
    for( my $i = 0; $i < @_ ; $i += 2 ) {
        next if $_[$i] !~ /^(mime|method|scheme|host|path|query)$/;
        $arg{$_[$i]} = $_[$i+1];
        splice @_, $i, 2;
        $i -= 2;
    }
    croak "Odd number of arguments" if @_ % 2;

    # the proxy must be initialised
    $self->init;

    # prepare the variables for the closure
    my ( $mime, $method, $scheme, $host, $path, $query ) =
      @arg{qw( mime method scheme host path query )};

    if ( defined $mime && $mime ne '' ) {
        $mime =~ m!/! or croak "Invalid MIME type definition: $mime";
        $mime =~ s/\*/$RX{token}/;    #turn it into a regex
        $mime = qr/^$mime(?:$|\s*;?)/;
    }

    my @method = split /\s*,\s*/, $method;
    for (@method) { croak "Invalid method: $_" if !/$RX{method}/ }
    $method = @method ? '(?:' . join ( '|', @method ) . ')' : '';
    $method = qr/^$method$/;

    my @scheme = split /\s*,\s*/, $scheme;
    for (@scheme) {
        croak "Unsupported scheme: $_"
          if !$self->is_protocol_supported($_);
    }
    $scheme = @scheme ? '(?:' . join ( '|', @scheme ) . ')' : '';
    $scheme = qr/$scheme/;

    $host  ||= '.*'; $host  = qr/$host/i;
    $path  ||= '.*'; $path  = qr/$path/;
    $query ||= '.*'; $query = qr/$query/;

    # push the filter and its match method on the correct stack
    while(@_) {
        my ($message, $filter ) = (shift, shift);
        croak "'$message' is not a filter stack"
          unless $message =~ /^(request|response)$/;

        croak "Not a Filter reference for filter queue $message"
          unless ref( $filter )
          && ( $filter->isa('HTTP::Proxy::HeaderFilter')
            || $filter->isa('HTTP::Proxy::BodyFilter') );

        my $stack;
        $stack = 'headers' if $filter->isa('HTTP::Proxy::HeaderFilter');
        $stack = 'body'    if $filter->isa('HTTP::Proxy::BodyFilter');

        # MIME can only match on reponse
        my $mime = $mime;
        undef $mime if $message eq 'request';

        # compute the match sub as a closure
        # for $self, $mime, $method, $scheme, $host, $path
        my $match = sub {
            return 0
              if ( defined $mime )
              && ( $self->response->content_type || '' ) !~ $mime;
            return 0 if ( $self->{request}->method || '' ) !~ $method;
            return 0 if ( $self->{request}->uri->scheme    || '' ) !~ $scheme;
            return 0 if ( $self->{request}->uri->authority || '' ) !~ $host;
            return 0 if ( $self->{request}->uri->path      || '' ) !~ $path;
            return 0 if ( $self->{request}->uri->query     || '' ) !~ $query;
            return 1;    # it's a match
        };

        # push it on the corresponding FilterStack
        $self->{$stack}{$message}->push( [ $match, $filter ] );
        $filter->proxy( $self );
    }
}

sub is_protocol_supported {
    my ( $self, $scheme ) = @_;
    my $ok = 1;
    if ( !$self->agent->is_protocol_supported($scheme) ) {

        # double check, in case a dummy scheme was added
        # to be handled directly by a filter
        $ok = 0;
        $scheme eq $_ && $ok++ for @{ $self->agent->protocols_allowed };
    }
    $ok;
}

sub log {
    my $self  = shift;
    my $level = shift;
    my $fh    = $self->logfh;

    return unless $self->logmask & $level || $level == ERROR;

    my ( $prefix, $msg ) = ( @_, '' );
    my @lines = split /\n/, $msg;
    @lines = ('') if not @lines;

    flock( $fh, LOCK_EX );
    print $fh "[" . localtime() . "] ($$) $prefix: $_\n" for @lines;
    flock( $fh, LOCK_UN );
}

1;

__END__

=head1 NAME

HTTP::Proxy - A pure Perl HTTP proxy

=head1 SYNOPSIS

    use HTTP::Proxy;

    # initialisation
    my $proxy = HTTP::Proxy->new( port => 3128 );

    # alternate initialisation
    my $proxy = HTTP::Proxy->new;
    $proxy->port( 3128 ); # the classical accessors are here!

    # this is a MainLoop-like method
    $proxy->start;

=head1 DESCRIPTION

This module implements a HTTP proxy, using a HTTP::Daemon to accept
client connections, and a LWP::UserAgent to ask for the requested pages.

The most interesting feature of this proxy object is its ability to
filter the HTTP requests and responses through user-defined filters.

Once the proxy is created, with the C<new()> method, it is possible
to alter its behaviour by adding so-called "filters". This is
done by the C<push_filter()> method. Once the filter is ready to
run, it can be launched, with the C<start()> method. This method
does not normally return until the proxy is killed or otherwise
stopped.

An important thing to note is that the proxy is (except when running
the C<NoFork> engine) a I<forking> proxy: it doesn't support passing
information between child processes, and you can count on reliable
information passing only during a single HTTP connection (request +
response).

=head1 FILTERS

You can alter the way the default HTTP::Proxy works by plugging callbacks
(filter objects, actually) at different stages of the request/response
handling.

When a request is received by the HTTP::Proxy object, it is filtered through
a standard filter that transform this request accordingly to RFC 2616
(by adding the C<Via:> header, and a few other transformations). This is
the default, bare minimum behaviour.

The response is also filtered in the same manner. There is a total of four
filter chains: C<request-headers>, C<request-body>, C<reponse-headers> and
C<response-body>.

You can add your own filters to the default ones with the
C<push_filter()> method. The method pushes a filter on the appropriate
filter stack.

    $proxy->push_filter( response => $filter );

The headers/body category is determined by the base class of the filter.
There are two base classes for filters, which are
C<HTTP::Proxy::HeaderFilter> and C<HTTP::Proxy::BodyFilter> (the names
are self-explanatory). See the documentation of those two classes
to find out how to write your own header or body filters.

The named parameter is used to determine the request/response part.

It is possible to push the same filter on the request and response
stacks, as in the following example:

    $proxy->push_filter( request => $filter, response => $filter );

If several filters match the message, they will be applied in the order
they were pushed on their filter stack.

Named parameters can be used to create the match routine. They are: 

    method - the request method
    scheme - the URI scheme         
    host   - the URI authority (host:port)
    path   - the URI path
    query  - the URI query string
    mime   - the MIME type (for a response-body filter)

The filters are applied only when all the the parameters match the
request or the response. All these named parameters have default values,
which are:

    method => 'OPTIONS,GET,HEAD,POST,PUT,DELETE,TRACE,CONNECT'
    scheme => 'http'
    host   => ''
    path   => ''
    query  => ''
    mime   => 'text/*'

The C<mime> parameter is a glob-like string, with a required C</>
character and a C<*> as a joker. Thus, C<*/*> matches I<all> responses,
and C<""> those with no C<Content-Type:> header. To match any
reponse (with or without a C<Content-Type:> header), use C<undef>.

The C<mime> parameter is only meaningful with the C<response-body>
filter stack. It is ignored if passed to any other filter stack.

The C<method> and C<scheme> parameters are strings consisting of
comma-separated values. The C<host> and C<path> parameters are regular
expressions.

A match routine is compiled by the proxy and used to check if a particular
request or response must be filtered through a particular filter.

It is also possible to push several filters on the same stack with
the same match subroutine:

    # convert italics to bold
    $proxy->push_filter(
        mime     => 'text/html',
        response => HTTP::Proxy::BodyFilter::tags->new(),
        response => HTTP::Proxy::BodyFilter::simple->new(
            sub { ${ $_[1] } =~ s!(</?)i>!$1b>!ig }
        )
    );

For more details regarding the creation of new filters, check the
C<HTTP::Proxy::HeaderFilter> and C<HTTP::Proxy::BodyFilter> documentation.

Here's an example of subclassing a base filter class:

    # fixes a common typo ;-)
    # but chances are that this will modify a correct URL
    {
        package FilterPerl;
        use base qw( HTTP::Proxy::BodyFilter );

        sub filter {
            my ( $self, $dataref, $message, $protocol, $buffer ) = @_;
            $$dataref =~ s/PERL/Perl/g;
        }
    }
    $proxy->push_filter( response => FilterPerl->new() );

Other examples can be found in the documentation for
C<HTTP::Proxy::HeaderFilter>, C<HTTP::Proxy::BodyFilter>,
C<HTTP::Proxy::HeaderFilter::simple>, C<HTTP::Proxy::BodyFilter::simple>.

    # a simple anonymiser
    # see eg/anonymiser.pl for the complete code
    $proxy->push_filter(
        mime    => undef,
        request => HTTP::Proxy::HeaderFilter::simple->new(
            sub { $_[0]->remove_header(qw( User-Agent From Referer Cookie )) },
        ),
        response => HTTP::Proxy::HeaderFilter::simple->new(
            sub { $_[0]->remove_header(qw( Set-Cookie )); },
        )
    );

IMPORTANT: If you use your own C<LWP::UserAgent>, you must install it
before your calls to C<push_filter()>, otherwise
the match method will make wrong assumptions about the schemes your
agent supports.

NOTE: It is likely that possibility of changing the agent or the daemon
may disappear in future versions.

=head1 METHODS

=head2 Constructor and initialisation

=over 4

=item new()

The C<new()> method creates a new HTTP::Proxy object. All attributes can
be passed as parameters to replace the default.

Parameters that are not C<HTTP::Proxy> attributes will be ignored and
passed to the chosen C<HTTP::Proxy::Engine> object.

=item init()

C<init()> initialise the proxy without starting it. It is usually not
needed.

This method is called by C<start()> if needed.

=item push_filter()

The C<push_filter()> method is used to add filters to the proxy.
It is fully described in section L<FILTERS>.

=back

=head2 Accessors and mutators

The HTTP::Proxy has several accessors and mutators.

Called with arguments, the accessor returns the current value.
Called with a single argument, it sets the current value and
returns the previous one, in case you want to keep it.

If you call a read-only accessor with a parameter, this parameter
will be ignored.

The defined accessors are (in alphabetical order):

=over 4

=item agent

The LWP::UserAgent object used internally to connect to remote sites.

=item chunk

The chunk size for the LWP::UserAgent callbacks.

=item client_socket (read-only)

The socket currently connected to the client. Mostly useful in filters.

=item client_headers

This attribute holds a reference to the client headers set up by
LWP::UserAgent
(C<Client-Aborted>, C<Client-Bad-Header-Line>, C<Client-Date>,
C<Client-Junk>, C<Client-Peer>, C<Client-Request-Num>,
C<Client-Response-Num>, C<Client-SSL-Cert-Issuer>,
C<Client-SSL-Cert-Subject>, C<Client-SSL-Cipher>, C<Client-SSL-Warning>,
C<Client-Transfer-Encoding>, C<Client-Warning>).

They are removed by the filter HTTP::Proxy::HeaderFilter::standard from
the request and response objects received by the proxy.

If a filter (such as a SSL certificate verification filter) need to
access them, it must do it through this accessor.

=item conn (read-only)

The number of connections processed by this HTTP::Proxy instance.

=item daemon

The HTTP::Daemon object used to accept incoming connections.
(You usually never need this.)

=item engine

The HTTP::Proxy::Engine object that manages the child processes.

=item hop_headers

This attribute holds a reference to the hop-by-hop headers
(C<Connection>, C<Keep-Alive>, C<Proxy-Authenticate>, C<Proxy-Authorization>,
C<TE>, C<Trailers>, C<Transfer-Encoding>, C<Upgrade>).

They are removed by the filter HTTP::Proxy::HeaderFilter::standard from
the request and response objects received by the proxy.

If a filter (such as a proxy authorisation filter) need to access them,
it must do it through this accessor.

=item host

The proxy HTTP::Daemon host (default: 'localhost').

This means that by default, the proxy answers only to clients on the
local machine. You can pass a specific interface address or C<"">/C<undef>
for any interface.

This default prevents your proxy to be used as an anonymous proxy
by script kiddies.

=item known_methods( @groups ) (read-only)

This method returns all HTTP (and extensions to HTTP) known to
C<HTTP::Proxy>. Methods are grouped by type. Known method groups are:
C<HTTP>, C<WebDAV> and C<DeltaV>.

Called with an empty list, this method will return all known methods.
This method is case-insensitive, and will C<carp()> if an unknown
group name is passed.

=item logfh

A filehandle to a logfile (default: *STDERR).

=item logmask( [$mask] )

Be verbose in the logs (default: NONE).

Here are the various elements that can be added to the mask (their values
are powers of 2, starting from 0 and listed here in ascending order):

    NONE    - Log only errors
    PROXY   - Proxy information
    STATUS  - Requested URL, reponse status and total number
              of connections processed
    PROCESS - Subprocesses information (fork, wait, etc.)
    SOCKET  - Information about low-level sockets
    HEADERS - Full request and response headers are sent along
    FILTERS - Filter information
    DATA    - Data received by the filters
    CONNECT - Data transmitted by the CONNECT method
    ENGINE  - Engine information
    ALL     - Log all of the above

If you only want status and process information, you can use:

    $proxy->logmask( STATUS | PROCESS );

Note that all the logging constants are not exported by default, but 
by the C<:log> tag. They can also be exported one by one.

=item loop (read-only)

Internal. False when the main loop is about to be broken.

=item max_clients

=item maxchild

The maximum number of child process the HTTP::Proxy object will spawn
to handle client requests (default: depends on the engine).

This method is currently delegated to the HTTP::Proxy::Engine object.

C<maxchild> is deprecated and will disappear.

=item max_connections

=item maxconn

The maximum number of TCP connections the proxy will accept before
returning from start(). 0 (the default) means never stop accepting
connections.

C<maxconn> is deprecated.

Note: C<max_connections> will be deprecated soon, for two reasons: 1)
it is more of an HTTP::Proxy::Engine attribute, 2) not all engines will
support it.

=item max_keep_alive_requests

=item maxserve

The maximum number of requests the proxy will serve in a single connection.
(same as C<MaxRequestsPerChild> in Apache)

C<maxserve> is deprecated.

=item port

The proxy C<HTTP::Daemon> port (default: 8080).

=item request

The request originaly received by the proxy from the user-agent, which
will be modified by the request filters.

=item response

The response received from the origin server by the proxy. It is
normally C<undef> until the proxy actually receives the beginning
of a response from the origin server.

If one of the request filters sets this attribute, it "short-circuits"
the request/response scheme, and the proxy will return this response
(which is NOT filtered through the response filter stacks) instead of
the expected origin server response. This is useful for caching (though
Squid does it much better) and proxy authentication, for example.

=item stash

The stash is a hash where filters can store data to share between them.

The stash() method can be used to set the whole hash (with a HASH reference).
To access individual keys simply do:

    $proxy->stash( 'bloop' );

To set it, type:

    $proxy->stash( bloop => 'owww' );

It's also possibly to get a reference to the stash:

    my $s = $filter->proxy->stash();
    $s->{bang} = 'bam';

    # $proxy->stash( 'bang' ) will now return 'bam'

B<Warning:> since the proxy forks for each TCP connection, the data is
only shared between filters in the same child process.

=item timeout

The timeout used by the internal LWP::UserAgent (default: 60).

=item url (read-only)

The url where the proxy can be reached.

=item via

The content of the Via: header. Setting it to an empty string will
prevent its addition. (default: C<$hostname (HTTP::Proxy/$VERSION)>)

=item x_forwarded_for

If set to a true value, the proxy will send the C<X-Forwarded-For:> header.
(default: true)

=back

=head2 Connection handling methods

=over 4

=item start()

This method works like Tk's C<MainLoop>: you hand over control to the
C<HTTP::Proxy> object you created and configured.

If C<maxconn> is not zero, C<start()> will return after accepting
at most that many connections. It will return the total number of
connexions.

=item serve_connections()

This is the internal method used to handle each new TCP connection
to the proxy.

=back

=head2 Other methods

=over 4

=item log( $level, $prefix, $message )

Adds C<$message> at the end of C<logfh>, if $level matches C<logmask>.
The C<log()> method also prints a timestamp.

The output looks like:

    [Thu Dec  5 12:30:12 2002] ($$) $prefix: $message

where C<$$> is the current processus id.

If C<$message> is a multiline string, several log lines will be output,
each line starting with C<$prefix>.

=item is_protocol_supported( $scheme )

Returns a boolean indicating if $scheme is supported by the proxy.

This method is only used internaly.

It is essential to allow HTTP::Proxy users to create "pseudo-schemes"
that LWP doesn't know about, but that one of the proxy filters can handle
directly. New schemes are added as follows:

    $proxy->init();    # required to get an agent
    $proxy->agent->protocols_allowed(
        [ @{ $proxy->agent->protocols_allowed }, 'myhttp' ] );

=item new_connection()

Increase the proxy's TCP connections counter. Only used by
C<HTTP::Proxy::Engine> objects.

=back

=head2 Apache-like attributes

C<HTTP::Proxy> has several Apache-like attributes that control the
way the HTTP and TCP connections are handled.

The following attributes control the TCP connection. They are passed to
the underlying C<HTTP::Proxy::Engine>, which may (or may not) use them
to change its behaviour.

=over 4

=item start_servers

Number of child process to fork at the beginning.

=item max_clients

Maximum number of concurrent TCP connections (i.e. child processes).

=item max_requests_per_child

Maximum number of TCP connections handled by the same child process.

=item min_spare_servers

Minimum number of inactive child processes.

=item max_spare_servers

Maximum number of inactive child processes.

=back

Those attributes control the HTTP connection:

=over 4

=item keep_alive

Support for keep alive HTTP connections.

=item max_keep_alive_requests

Maximum number of HTTP connections within a single TCP connection.

=item keep_alive_timeout

Timeout for keep-alive connection.

=back

=head1 EXPORTED SYMBOLS

No symbols are exported by default. The C<:log> tag exports all the
logging constants.

=head1 BUGS

This module does not work under Windows, but I can't see why, and do not
have a development platform under that system. Patches and explanations
very welcome.

I guess it is because C<fork()> is not well supported.

    $proxy->maxchild(0);

=over 4

=item However, David Fishburn says:

This did not work for me under WinXP - ActiveState Perl 5.6, but it DOES        
work on WinXP ActiveState Perl 5.8. 

=back

Several people have tried to help, but we haven't found a way to make it work
correctly yet.

As from version 0.16, the default engine is C<HTTP::Proxy::Engine::NoFork>.
Let me know if it works better.

=head1 SEE ALSO

L<HTTP::Proxy::Engine>, L<HTTP::Proxy::BodyFilter>,
L<HTTP::Proxy::HeaderFilter>, the examples in F<eg/>.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

The module has its own web page at L<http://http-proxy.mongueurs.net/>
complete with older versions and repository snapshot.

There are also two mailing-lists: http-proxy@mongueurs.net for general
discussion about C<HTTP::Proxy> and http-proxy-cvs@mongueurs.net for
CVS commits emails.

=head1 THANKS

Many people helped me during the development of this module, either on
mailing-lists, IRC or over a beer in a pub...

So, in no particular order, thanks to the libwww-perl team for such a
terrific suite of modules, perl-qa (tips for testing), the French Perl
I<Mongueurs> (for code tricks, beers and encouragements) and my growing
user base... C<;-)>

I'd like to particularly thank Dan Grigsby, who's been using
C<HTTP::Proxy> since 2003 (before the filter classes even existed).  He is
apparently making a living from a product based on C<HTTP::Proxy>. Thanks
a lot for your confidence in my work!

=head1 COPYRIGHT

Copyright 2002-2008, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut


