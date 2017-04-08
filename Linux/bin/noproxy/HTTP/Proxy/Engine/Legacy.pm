package HTTP::Proxy::Engine::Legacy;
use strict;
use POSIX 'WNOHANG';
use HTTP::Proxy;

our @ISA = qw( HTTP::Proxy::Engine );
our %defaults = (
    max_clients => 12,
);

__PACKAGE__->make_accessors( qw( kids select ), keys %defaults );

sub start {
    my $self = shift;
    $self->kids( [] );
    $self->select( IO::Select->new( $self->proxy->daemon ) );
}

sub run {
    my $self   = shift;
    my $proxy  = $self->proxy;
    my $kids   = $self->kids;

    # check for new connections
    my @ready = $self->select->can_read(1);
    for my $fh (@ready) {    # there's only one, anyway

        # single-process proxy (useful for debugging)
        if ( $self->max_clients == 0 ) {
            $proxy->max_keep_alive_requests(1);  # do not block simultaneous connections
            $proxy->log( HTTP::Proxy::PROCESS, "PROCESS",
                        "No fork allowed, serving the connection" );
            $proxy->serve_connections($fh->accept);
            $proxy->new_connection;
            next;
        }

        if ( @$kids >= $self->max_clients ) {
            $proxy->log( HTTP::Proxy::ERROR, "PROCESS",
                        "Too many child process, serving the connection" );
            $proxy->serve_connections($fh->accept);
            $proxy->new_connection;
            next;
        }

        # accept the new connection
        my $conn  = $fh->accept;
        my $child = fork;
        if ( !defined $child ) {
            $conn->close;
            $proxy->log( HTTP::Proxy::ERROR, "PROCESS", "Cannot fork" );
            $self->max_clients( $self->max_clients - 1 )
              if $self->max_clients > @$kids;
            next;
        }

        # the parent process
        if ($child) {
            $conn->close;
            $proxy->log( HTTP::Proxy::PROCESS, "PROCESS", "Forked child process $child" );
            push @$kids, $child;
        }

        # the child process handles the whole connection
        else {
            $SIG{INT} = 'DEFAULT';
            $proxy->serve_connections($conn);
            exit;    # let's die!
        }
    }

    $self->reap_zombies if @$kids;
}

sub stop {
    my $self = shift;
    my $kids = $self->kids;

    # wait for remaining children
    # EOLOOP
    kill INT => @$kids;
    $self->reap_zombies while @$kids;
}

# private reaper sub
sub reap_zombies {
    my $self  = shift;
    my $kids  = $self->kids;
    my $proxy = $self->proxy;

    while (1) {
        my $pid = waitpid( -1, WNOHANG );
        last if $pid == 0 || $pid == -1;    # AS/Win32 returns negative PIDs
        @$kids = grep { $_ != $pid } @$kids;
        $proxy->{conn}++;    # Cannot use the interface for RO attributes
        $proxy->log( HTTP::Proxy::PROCESS, "PROCESS", "Reaped child process $pid" );
        $proxy->log( HTTP::Proxy::PROCESS, "PROCESS", @$kids . " remaining kids: @$kids" );
    }
}

1;

__END__

=head1 NAME

HTTP::Proxy::Engine::Legacy - The "older" HTTP::Proxy engine

=head1 SYNOPSIS

    my $proxy = HTTP::Proxy->new( engine => 'Legacy' );

=head1 DESCRIPTION

This engine reproduces the older child creation algorithm of HTTP::Proxy.

=head1 METHODS

The module defines the following methods, used by HTTP::Proxy main loop:

=over 

=item start()

Initialise the engine.

=item run()

Implements the forking logic: a new process is forked for each new
incoming TCP connection.

=item stop()

Reap remaining child processes.

=back

The following method is used by the engine internally:

=over 4

=item reap_zombies()

Process the dead child processes.

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

