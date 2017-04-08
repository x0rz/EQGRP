package HTTP::Proxy::HeaderFilter::standard;

use strict;
use HTTP::Proxy;
use HTTP::Headers::Util qw( split_header_words );
use HTTP::Proxy::HeaderFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::HeaderFilter );

# known hop-by-hop headers
my %hopbyhop = map { $_ => 1 }
  qw( Connection Keep-Alive Proxy-Authenticate Proxy-Authorization
      TE Trailers Transfer-Encoding Upgrade Proxy-Connection Public );

# standard proxy header filter (RFC 2616)
sub filter {
    my ( $self, $headers, $message ) = @_;

    # the Via: header
    my $via = $message->protocol() || '';
    if ( $self->proxy->via and $via =~ s!HTTP/!! ) {
        $via .= " " . $self->proxy->via;
        $headers->header(
            Via => join ', ',
            $message->headers->header('Via') || (), $via
        );
    }

    # the X-Forwarded-For header
    $headers->push_header(
        X_Forwarded_For => $self->proxy->client_socket->peerhost )
      if $message->isa( 'HTTP::Request' ) && $self->proxy->x_forwarded_for;

    # make a list of hop-by-hop headers
    my %h2h = %hopbyhop;
    my $hop = HTTP::Headers->new();
    my $client = HTTP::Headers->new();
    $h2h{ $_->[0] } = 1
      for map { split_header_words($_) } $headers->header('Connection');

    # hop-by-hop headers are set aside
    # as well as LWP::UserAgent Client-* headers
    $headers->scan(
        sub {
            my ( $k, $v ) = @_;
            if ( $h2h{$k} ) {
                $hop->push_header( $k => $v );
                $headers->remove_header($k);
            }
            if( $k =~ /^Client-/ ) {
                $client->push_header( $k => $v );
                $headers->remove_header($k);
            }
        }
    );

    # set the hop-by-hop and client  headers in the proxy
    # only the end-to-end headers are left in the message
    $self->proxy->hop_headers($hop);
    $self->proxy->client_headers($client);

    # handle Max-Forwards
    if ( $message->isa('HTTP::Request')
        and defined $headers->header('Max-Forwards') ) {
        my ( $max, $method ) =
          ( $headers->header('Max-Forwards'), $message->method );
        if ( $max == 0 ) {
            # answer directly TRACE ou OPTIONS
            if ( $method eq 'TRACE' ) {
                my $response =
                  HTTP::Response->new( 200, 'OK',
                    HTTP::Headers->new( Content_Type => 'message/http'
                    , Content_Length => 0),
                    $message->as_string );
                $self->proxy->response($response);
            }
            elsif ( $method eq 'OPTIONS' ) {
                my $response = HTTP::Response->new(200);
                $response->header( Allow => join ', ', @HTTP::Proxy::METHODS );
                $self->proxy->response($response);
            }
        }
        # The Max-Forwards header field MAY be ignored for all
        # other methods defined by this specification (RFC 2616)
        elsif ( $method =~ /^(?:TRACE|OPTIONS)/ ) {
            $headers->header( 'Max-Forwards' => --$max );
        }
    }

    # remove some headers
    $headers->remove_header($_) for (

        # no encoding accepted (gzip, compress, deflate)
        qw( Accept-Encoding ),
    );
}

1;

__END__

=head1 NAME

HTTP::Proxy::HeaderFilter::standard - An internal filter to respect RFC2616

=head1 DESCRIPTION

This is an internal filter used by HTTP::Proxy to enforce behaviour
compliant with RFC 2616.

=head1 METHOD

This filter implements a single method that is called automatically:

=over 4

=item filter()

Enforce RFC 2616-compliant behaviour, by adding the C<Via:> and
C<X-Forwarded-For:> headers (except when the proxy was instructed not
to add them), decrementing the C<Max-Forwards:> header and removing
the hop-by-hop and LWP::UserAgent headers.

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::HeaderFilter>, RFC 2616.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

Thanks to Gisle Aas, for directions regarding the handling of the
hop-by-hop headers.

=head1 COPYRIGHT

Copyright 2003-2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

