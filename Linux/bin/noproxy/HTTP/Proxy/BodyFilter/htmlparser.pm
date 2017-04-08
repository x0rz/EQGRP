package HTTP::Proxy::BodyFilter::htmlparser;

use strict;
use Carp;
use HTTP::Proxy::BodyFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::BodyFilter );

sub init {
    croak "First parameter must be a HTML::Parser object"
      unless $_[1]->isa('HTML::Parser');

    my $self = shift;
    $self->{_parser} = shift;

    my %args = (@_);
    $self->{rw} = delete $args{rw};
}

sub filter {
    my ( $self, $dataref, $message, $protocol, $buffer ) = @_;

    @{ $self->{_parser} }{qw( output message protocol )} =
      ( "", $message, $protocol );

    $self->{_parser}->parse($$dataref);
    $self->{_parser}->eof if not defined $buffer;    # last chunk
    $$dataref = $self->{_parser}{output} if $self->{rw};
}

sub will_modify { $_[0]->{rw} }

1;

__END__

=head1 NAME

HTTP::Proxy::BodyFilter::htmlparser - Filter using HTML::Parser

=head1 SYNOPSIS

    use HTTP::Proxy::BodyFilter::htmlparser;

    # $parser is a HTML::Parser object
    $proxy->push_filter(
        mime     => 'text/html',
        response => HTTP::Proxy::BodyFilter::htmlparser->new( $parser );
    );

=head1 DESCRIPTION

The HTTP::Proxy::BodyFilter::htmlparser lets you create a
filter based on the HTML::Parser object of your choice.

This filter takes a HTML::Parser object as an argument to its constructor.
The filter is either read-only or read-write. A read-only filter will
not allow you to change the data on the fly. If you request a read-write
filter, you'll have to rewrite the response-body completely.

With a read-write filter, you B<must> recreate the whole body data. This
is mainly due to the fact that the HTML::Parser has its own buffering
system, and that there is no easy way to correlate the data that triggered
the HTML::Parser event and its original position in the chunk sent by the
origin server. See below for details.

Note that a simple filter that modify the HTML text (not the tags) can
be created more easily with HTTP::Proxy::BodyFilter::htmltext.

=head2 Creating a HTML::Parser that rewrites pages

A read-write filter is declared by passing C<rw =E<gt> 1> to the constructor:

     HTTP::Proxy::BodyFilter::htmlparser->new( $parser, rw => 1 );

To be able to modify the body of a message, a filter created with
HTTP::Proxy::BodyFilter::htmlparser must rewrite it completely. The
HTML::Parser object can update a special attribute named C<output>.
To do so, the HTML::Parser handler will have to request the C<self>
attribute (that is to say, require access to the parser itself) and
update its C<output> key.

The following attributes are added to the HTML::Parser object by this filter:

=over 4

=item output

A string that will hold the data sent back by the proxy.

This string will be used as a replacement for the body data only
if the filter is read-write, that is to say, if it was initialised with
C<rw =E<gt> 1>.

Data should always be B<appended> to C<$parser-E<gt>{output}>.

=item message

A reference to the HTTP::Message that triggered the filter.

=item protocol

A reference to the HTTP::Protocol object.

=back

=head1 METHODS

This filter defines three methods, called automatically:

=over 4

=item filter()

The C<filter()> method handles all the interactions with the HTML::Parser
object.

=item init()

Initialise the filter with the HTML::Parser object passed to the constructor.

=item will_modify()

This method returns a boolean value that indicates to the system
if it will modify the data passing through. The value is actually
the value of the C<rw> parameter passed to the constructor.

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::Bodyfilter>,
L<HTTP::Proxy::BodyFilter::htmltext>.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

=head1 COPYRIGHT

Copyright 2003-2006, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

