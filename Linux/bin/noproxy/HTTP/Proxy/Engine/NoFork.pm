package HTTP::Proxy::Engine::NoFork;
use strict;

our @ISA = qw( HTTP::Proxy::Engine );

__PACKAGE__->make_accessors( 'select' );

sub start {
    my $self = shift;
    my $proxy = $self->proxy;

    $self->select( IO::Select->new( $proxy->daemon ) );

    # clients will not block the proxy by keeping the connection open
    $proxy->max_keep_alive_requests( 1 );
}

sub run {
    my $self  = shift;
    my $proxy = $self->proxy;

    # check for new connections
    for my $fh ( $self->select->can_read() ) {    # there's only one, anyway

        # single-process proxy
        $proxy->serve_connections( $fh->accept );
        $proxy->new_connection;
    }
}

1;

__END__

=head1 NAME

HTTP::Proxy::Engine::NoFork - A basic, non forking HTTP::Proxy engine

=head1 SYNOPSIS

    use HTTP::Proxy;
    my $proxy = HTTP::Proxy->new( engine => 'NoFork' );

=head1 DESCRIPTION

The HTTP::Proxy::Engine::NoFork engine runs the proxy with forking.

This 

=head1 METHODS

=over 4

=item start()

Initialise the engine.

=item run()

Implements the non-forking logic by calling $proxy->serve_requests()
directly.

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::Engine>.

=head1 AUTHOR

Philippe "BooK" Bruhat, C<< <book@cpan.org> >>.

=head1 COPYRIGHT

Copyright 2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

