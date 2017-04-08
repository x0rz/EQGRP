package HTTP::Proxy::HeaderFilter::simple;

use strict;
use Carp;
use HTTP::Proxy::HeaderFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::HeaderFilter );

my $methods = join '|', qw( begin filter end );
$methods = qr/^(?:$methods)$/;

sub init {
    my $self = shift;

    croak "Constructor called without argument" unless @_;
    if ( @_ == 1 ) {
        croak "Single parameter must be a CODE reference"
          unless ref $_[0] eq 'CODE';
        $self->{_filter} = $_[0];
    }
    else {
        $self->{_filter} = sub { };    # default
        while (@_) {
            my ( $name, $code ) = splice @_, 0, 2;

            # basic error checking
            croak "Parameter to $name must be a CODE reference"
              unless ref $code eq 'CODE';
            croak "Unkown method $name" unless $name =~ $methods;

            $self->{"_$name"} = $code;
        }
    }
}

# transparently call the actual methods
sub begin       { goto &{ $_[0]{_begin} }; }
sub filter      { goto &{ $_[0]{_filter} }; }
sub end         { goto &{ $_[0]{_end} }; }

sub can {
    my ( $self, $method ) = @_;
    return $method =~ $methods
      ? $self->{"_$method"}
      : UNIVERSAL::can( $self, $method );
}

1;

__END__

=head1 NAME

HTTP::Proxy::HeaderFilter::simple - A class for creating simple filters

=head1 SYNOPSIS

    use HTTP::Proxy::HeaderFilter::simple;

    # a simple User-Agent filter
    my $filter = HTTP::Proxy::HeaderFilter::simple->new(
        sub { $_[1]->header( User_Agent => 'foobar/1.0' ); }
    );
    $proxy->push_filter( request => $filter );

=head1 DESCRIPTION

HTTP::Proxy::HeaderFilter::simple can create BodyFilter without going
through the hassle of creating a full-fledged class. Simply pass
a code reference to the filter() method of your filter to the constructor,
and you'll get the adequate filter.

=head2 Constructor calling convention

The constructor is called with a single code reference.
The code reference must conform to the standard filter() signature
for header filters:

    sub filter { my ( $self, $headers, $message) = @_; ... }

This code reference is used for the filter() method.

=head1 METHODS

This filter "factory" defines the standard HTTP::Proxy::HeaderFilter
methods, but those are only, erm, "proxies" to the actual CODE references
passed to the constructor. These "proxy" methods are:

=over 4

=item filter()

=item begin()

=item end()

=back

Two other methods are actually HTTP::Proxy::HeaderFilter::simple methods,
and are called automatically:

=over 4

=item init()

Initalise the filter instance with the code references passed to the
constructor.

=item can()

Return the actual code reference that will be run, and not the "proxy"
methods. If called with any other name than C<begin> and C<filter>,
it calls UNIVERSAL::can() instead.

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::HeaderFilter>.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

=head1 COPYRIGHT

Copyright 2003-2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

