package HTTP::Proxy::BodyFilter::simple;

use strict;
use Carp;
use HTTP::Proxy::BodyFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::BodyFilter );

my $methods = join '|', qw( begin filter end will_modify );
$methods = qr/^(?:$methods)$/;

sub init {
    my $self = shift;

    croak "Constructor called without argument" unless @_;

    $self->{_will_modify} = 1;

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
              if $name ne 'will_modify' && ref $code ne 'CODE';
            croak "Unkown method $name"
              unless $name =~ $methods;

            $self->{"_$name"} = $code;
        }
    }
}

# transparently call the actual methods
sub begin       { goto &{ $_[0]{_begin} }; }
sub filter      { goto &{ $_[0]{_filter} }; }
sub end         { goto &{ $_[0]{_end} }; }

sub will_modify { return $_[0]{_will_modify} }

sub can {
    my ( $self, $method ) = @_;
    return $method =~ $methods
      ? $self->{"_$method"}
      : UNIVERSAL::can( $self, $method );
}

1;

__END__

=head1 NAME

HTTP::Proxy::BodyFilter::simple - A class for creating simple filters

=head1 SYNOPSIS

    use HTTP::Proxy::BodyFilter::simple;

    # a simple s/// filter
    my $filter = HTTP::Proxy::BodyFilter::simple->new(
        sub { ${ $_[1] } =~ s/foo/bar/g; }
    );
    $proxy->push_filter( response => $filter );

=head1 DESCRIPTION

HTTP::Proxy::BodyFilter::simple can create BodyFilter without going
through the hassle of creating a full-fledged class. Simply pass
a code reference to the C<filter()> method of your filter to the constructor,
and you'll get the adequate filter.

=head2 Constructor calling convention

The constructor can be called in several ways, which are shown in the
synopsis:

=over 4

=item single code reference

The code reference must conform to the standard filter() signature:

    sub filter {
        my ( $self, $dataref, $message, $protocol, $buffer ) = @_;
        ...
    }

It is assumed to be the code for the C<filter()> method.
See HTTP::Proxy::BodyFilter.pm for more details about the C<filter()> method.

=item name/coderef pairs

The name is the name of the method (C<filter>, C<begin>, C<end>)
and the coderef is the method itself.

See HTTP::Proxy::BodyFilter for the methods signatures.

=back

=head1 METHODS

This filter "factory" defines the standard HTTP::Proxy::BodyFilter
methods, but those are only, erm, "proxies" to the actual CODE references
passed to the constructor. These "proxy" methods are:

=over 4

=item filter()

=item begin()

=item end()

=back

Two other methods are actually HTTP::Proxy::BodyFilter::simple methods,
and are called automatically:

=over 4

=item init()

Initalise the filter instance with the code references passed to the
constructor.

=item can()

Return the actual code reference that will be run, and not the "proxy"
methods. If called with any other name than C<begin>, C<end> and
C<filter>, calls UNIVERSAL::can() instead.

=back

There is also a method that returns a boolean value:

=over 4

=item will_modify()

The C<will_modify()> method returns a scalar value (boolean) indicating
if the filter may modify the body data. The default method returns a
true value, so you only need to set this value when you are I<absolutely
certain> that the filter will not modify data (or at least not modify
its final length).

Here's a simple example:

    $filter = HTTP::Proxy::BodyFilter::simple->new(
        filter => sub { ${ $_[1] } =~ s/foo/bar/g; },
        will_modify => 0,    # "foo" is the same length as "bar"
    );

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::BodyFilter>.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

=head1 COPYRIGHT

Copyright 2003-2006, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

