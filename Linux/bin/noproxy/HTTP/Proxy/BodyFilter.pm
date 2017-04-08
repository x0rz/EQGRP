package HTTP::Proxy::BodyFilter;

use strict;
use Carp;

sub new {
    my $class = shift;
    my $self = bless {}, $class;
    $self->init(@_) if $self->can('init');
    return $self;
}

sub proxy {
    my ( $self, $new ) = @_;
    return $new ? $self->{_hpbf_proxy} = $new : $self->{_hpbf_proxy};
}

sub filter {
    croak "HTTP::Proxy::HeaderFilter cannot be used as a filter";
}

sub will_modify { 1 } # by default, we expect the filter to modify data

1;

__END__

=head1 NAME

HTTP::Proxy::BodyFilter - A base class for HTTP messages body filters

=head1 SYNOPSIS

    package MyFilter;

    use base qw( HTTP::Proxy::BodyFilter );

    # a simple modification, that may break things
    sub filter {
        my ( $self, $dataref, $message, $protocol, $buffer ) = @_;
        $$dataref =~ s/PERL/Perl/g;
    }

    1;

=head1 DESCRIPTION

The HTTP::Proxy::BodyFilter class is used to create filters for
HTTP request/response body data.

=head2 Creating a BodyFilter

A BodyFilter is just a derived class that implements some methods
called by the proxy. Of all the methods presented below, only
C<filter()> B<must> be defined in the derived class.

=over 4

=item filter()

The signature of the filter() method is the following:

    sub filter {
        my ( $self, $dataref, $message, $protocol, $buffer ) = @_;
        ...
    }

where $self is the filter object, $dataref is a reference to the chunk
of body data received, 
$message is a reference to either a HTTP::Request or a HTTP::Response
object, and $protocol is a reference to the LWP::Protocol protocol object.

Note that this subroutine signature looks a lot like that of the call-
backs of LWP::UserAgent (except that $message is either a HTTP::Request
or a HTTP::Response object).

$buffer is a reference to a buffer where some of the unprocessed data
can be stored for the next time the filter will be called (see L</Using
a buffer to store data for a later use> for details). Thanks to the
built-in HTTP::Proxy::BodyFilter::* filters, this is rarely needed.

It is possible to access the headers of the message with
C<< $message->headers() >>. This HTTP::Headers object is the one
that was sent to the client
(if the filter is on the response stack) or origin server (if the filter
is on the request stack). Modifying it in the filter() method is useless,
since the headers have already been sent.

Since $dataref is a I<reference> to the data string, the referent
can be modified and the changes will be transmitted through the
filters that follows, until the data reaches its recipient.

A HTTP::Proxy::BodyFilter object is a blessed hash, and the base class
reserves only hash keys that start with C<_hpbf>.

=item new()

The constructor is defined for all subclasses. Initialisation tasks
(if any) for subclasses should be done in the C<init()> method (see below).

=item init()

This method is called by the C<new()> constructeur to perform all
initisalisation tasks. It's called once in the filter lifetime.

It receives all the parameters passed to C<new()>.

=item begin()

Some filters might require initialisation before they are able to handle
the data. If a C<begin()> method is defined in your subclass, the proxy
will call it before sending data to the C<filter()> method.

It's called once per HTTP message handled by the filter, before data
processing begins.

The method signature is as follows:

    sub begin {
        my ( $self, $message ) = @_
        ...
    }

=item end()

Some filters might require finalisation after they are finished handling
the data. If a C<end()> method is defined in your subclass, the proxy
will call it after it has finished sending data to the C<filter()> method.

It's called once per HTTP message handled by the filter, after all data
processing is done.

This method does not expect any parameters.

=item will_modify()

This method return a boolean value that indicate if the filter will
modify the body data on the fly.

The default implementation returns a I<true> value.

=back

=head2 Using a buffer to store data for a later use

Some filters cannot handle arbitrary data: for example a filter that
basically lowercases tag name will apply a simple regex
such as C<s/E<lt>\s*(\w+)([^E<gt>]*)E<gt>/E<lt>\L$1\E$2E<gt>/g>.
But the filter will fail is the chunk of data contains a tag
that is cut before the final C<E<gt>>.

It would be extremely complicated and error-prone to let each filter
(and its author) do its own buffering, so the HTTP::Proxy architecture
handles this too. The proxy passes to each filter, each time it is called,
a reference to an empty string ($buffer in the above signature) that
the filter can use to store some data for next run.

When the reference is C<undef>, it means that the filter cannot
store any data, because this is the very last run, needed to gather
all the data left in all buffers.

It is recommended to store as little data as possible in the buffer,
so as to avoid (badly) reproducing what HTTP::Proxy::BodyFilter::complete
does.

In particular, you have to remember that all the data that remains in
the buffer after the last piece of data is received from the origin
server will be sent back to your filter in one big piece.

=head2 The store and forward approach

HTTP::Proxy implements a I<store and forward> mechanism, for those filters
which need to have the whole message body to work. It's enabled simply by
pushing the HTTP::Proxy::BodyFilter::complete filter on the filter stack.

The data is stored in memory by the "complete" filter, which passes it
on to the following filter once the full message body has been received.

=head2 Standard BodyFilters

Standard HTTP::Proxy::BodyFilter classes are lowercase.

The following BodyFilters are included in the HTTP::Proxy distribution:

=over 4

=item lines

This filter makes sure that the next filter in the filter chain will
only receive complete lines. The "chunks" of data received by the
following filters with either end with C<\n> or will be the last
piece of data for the current HTTP message body.

=item htmltext

This class lets you create a filter that runs a given code reference
against text included in a HTML document (outside C<E<lt>scriptE<gt>>
and C<E<lt>styleE<gt>> tags). HTML entities are not included in the text.

=item htmlparser

Creates a filter from a HTML::Parser object.

=item simple

This class lets you create a simple body filter from a code reference.

=item save

Store the message body to a file.

=item complete

This filter stores the whole message body in memory, thus allowing
some actions to be taken only when the full page has been received
by the proxy.

=item tags

The HTTP::Proxy::BodyFilter::tags filter makes sure that the next filter
in the filter chain will only receive complete tags. The current
implementation is not 100% perfect, though.

=back

Please read each filter's documentation for more details about their use.

=head1 USEFUL METHODS FOR SUBCLASSES

Some methods are available to filters, so that they can eventually use
the little knowledge they might have of HTTP::Proxy's internals. They
mostly are accessors.

=over 4

=item proxy()

Gets a reference to the HTTP::Proxy objects that owns the filter.
This gives access to some of the proxy methods.

=back

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::HeaderFilter>.

=head1 COPYRIGHT

Copyright 2003-2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

