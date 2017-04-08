package HTTP::Proxy::Engine;
use strict;
use Carp;

my %engines = (
    MSWin32 => 'NoFork',
    default => 'Legacy',
);

# required accessors
__PACKAGE__->make_accessors( qw( max_clients ));

sub new {
    my $class  = shift;
    my %params = @_;

    # the front-end
    if ( $class eq 'HTTP::Proxy::Engine' ) {
        my $engine = delete $params{engine};
        $engine = $engines{$^O} || $engines{default}
          unless defined $engine;

        $class = "HTTP::Proxy::Engine::$engine";
        eval "require $class";
        croak $@ if $@;
    }

    # some error checking
    croak "No proxy defined"
      unless exists $params{proxy};
    croak "$params{proxy} is not a HTTP::Proxy object"
      unless UNIVERSAL::isa( $params{proxy}, 'HTTP::Proxy' );

    # so we are an actual engine
    no strict 'refs';
    return bless {
        %{"$class\::defaults"},
        %params
    }, $class;
}

# run() should be defined in subclasses
sub run {
    my $self = shift;
    my $class = ref $self;
    croak "$class doesn't define a run() method";
}

sub proxy { $_[0]{proxy} }

# class method
sub make_accessors {
    my $class = shift;

    for my $attr (@_) {
        no strict 'refs';
        *{"$class\::$attr"} = sub {
            $_[0]{$attr} = $_[1] if defined $_[1];
            $_[0]{$attr};
        };
    }
}

1;

__END__

=head1 NAME

HTTP::Proxy::Engine - Generic child process manager engine for HTTP::Proxy

=head1 SYNOPSIS

    use HTTP::Proxy;

    # use the default engine for your system
    my $proxy = HTTP::Proxy->new();

    # choose one
    my $proxy = HTTP::Proxy->new( engine => 'Old' );

=head1 DESCRIPTION

The HTTP::Proxy::Engine class is a front-end to actual proxy
engine classes.

The role of an engine is to implement the main fork+serve loop
with all the required bookkeeping. This is also a good way to
test various implementation and/or try out new algorithms
without too much difficulties.

=head1 METHODS

=over 4

=item new()

Create a new engine. The parameter C<engine> is used to decide which
kind of engine will be created. Other parameters are passed to the
underlying engine.

This method also implement the subclasses constructor (they obviously
do not need the C<engine> parameter).

=back

=head1 CREATING YOUR OWN ENGINE

It is possible to create one's own engine, by creating
a simple subclass of HTTP::Proxy::Engine with the following
methods:

=over 4

=item start()

This method should handle any initialisation required when the
engine starts.

=item run()

This method is the main loop of the master process.
It defines how child processes are forked, checked and killed.

The engine MUST have a run() method, and it will be called again
and again until the proxy exits.

$self->proxy->daemon returns the listening socket that can accept()
connections. The child must call $self->proxy->serve_connections()
on the returned socket to handle actual TCP connections.

=item stop()

This optional method should handle any cleanup procedures when the
engine stops (typically when the main proxy process is killed).

=back

A subclass may also define a C<%defaults> hash (with C<our>) that
contains the default values for the fields used internaly.

=head1 METHODS PROVIDED TO SUBCLASSES

HTTP::Proxy::Engine provides the following methods to its
subclasses:

=over 4

=item proxy()

Return the HTTP::Proxy object that runs the engine.

=item max_clients()

Get or set the maximum number of TCP clients, that is to say
the maximum number of forked child process.

Some engines may understand a value of C<0> as I<do not fork at all>.
This is what HTTP::Proxy::Engine::Legacy does.

=item make_accessors( @names )

Create accessors named after C<@names> in the subclass package.
All accessors are read/write. This is a utility method.

B<This is a class method.>

=back

=head1 AUTHOR

Philippe "BooK" Bruhat, C<< <book@cpan.org> >>.

=head1 COPYRIGHT

Copyright 2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

