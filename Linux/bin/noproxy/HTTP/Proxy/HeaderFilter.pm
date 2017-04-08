package HTTP::Proxy::HeaderFilter;

use strict;
use Carp;

sub new {
    my $class = shift;
    my $self = bless {}, $class;
    $self->init(@_) if $self->can('init');
    return $self;
}

sub filter {
    croak "HTTP::Proxy::HeaderFilter cannot be used as a filter";
}

sub proxy {
    my ( $self, $new ) = @_;
    return $new ? $self->{_hphf_proxy} = $new : $self->{_hphf_proxy};
}

1;

__END__

=head1 NAME

HTTP::Proxy::HeaderFilter - A base class for HTTP message header filters

=head1 SYNOPSIS

    package MyFilter;

    use base qw( HTTP::Proxy::HeaderFilter );

    # changes the User-Agent header in all requests
    # this filter must be pushed on the request stack
    sub filter {
        my ( $self, $headers, $message ) = @_;

        $message->headers->header( User_Agent => 'MyFilter/1.0' );
    }

    1;

=head1 DESCRIPTION

The HTTP::Proxy::HeaderFilter class is used to create filters for
HTTP request/response headers.

=head2 Creating a HeaderFilter

A HeaderFilter is just a derived class that implements some methods
called by the proxy. Of all the methods presented below, only
C<filter()> B<must> be defined in the derived class.

=over 4

=item filter()

The signature of the filter() method is the following:

    sub filter { my ( $self, $headers, $message) = @_; ... }

where $self is the filter object, $headers is a HTTP::Headers object,
and $message is either a HTTP::Request or a HTTP::Response object.

The $headers HTTP::Headers object is the one that will be sent to
the client (if the filter is on the response stack) or origin
server (if the filter is on the request stack). If $headers is
modified by the filter, the modified headers will be sent to the
client or server.

The init() method (if it exists) is called by the new() constructeur
to perform all initisalisation tasks. It's called once in the filter
lifetime.

A HTTP::Proxy::HeaderFilter object is a blessed hash, and the base class
reserves only hash keys that start with C<_hphf>.

=item new()

The constructor is defined for all subclasses. Initialisation tasks
(if any) for subclasses should be done in the C<init()> method (see below).

=item init()

This method is called by the C<new()> constructeur to perform all
initisalisation tasks. It's called once in the filter lifetime.

It receives all the parameters passed to C<new()>.

=back

=head2 Standard HeaderFilters

Standard HTTP::Proxy::HeaderFilter classes are lowercase.

The following HeaderFilters are included in the HTTP::Proxy distribution:

=over 4

=item simple

This class lets you create a simple header filter from a code reference.

=item standard

This is the filter that provides standard headers handling for HTTP::Proxy.
It is loaded automatically by HTTP::Proxy.

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

L<HTTP::Proxy>, L<HTTP::Proxy::BodyFilter>.

=head1 COPYRIGHT

Copyright 2003-2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

