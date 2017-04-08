package HTTP::Proxy::BodyFilter::tags;

use strict;
use Carp;
use HTTP::Proxy::BodyFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::BodyFilter );

sub filter {
    my ( $self, $dataref, $message, $protocol, $buffer ) = @_;
    return if not defined $buffer;    # last "tags"

    my $idx = rindex( $$dataref, '<' );
    if ( $idx > rindex( $$dataref, '>' ) ) {
        $$buffer = substr( $$dataref, $idx );
        $$dataref = substr( $$dataref, 0, $idx );
    }
}

sub will_modify { 0 }

1;

__END__

=head1 NAME

HTTP::Proxy::BodyFilter::tags - A filter that outputs only complete tags

=head1 SYNOPSIS

    use HTTP::Proxy::BodyFilter::tags;
    use MyFilter;    # this filter only works on complete tags

    my $filter = MyFilter->new();

    # note that both filters will be run on the same messages
    # (those with a MIME type of text/html)
    $proxy->push_filter(
        mime     => 'text/*',
        response => HTTP::Proxy::BodyFilter::tags->new
    );
    $proxy->push_filter( mime => 'text/html', response => $filter );

=head1 DESCRIPTION

The HTTP::Proxy::BodyFilter::tags filter makes sure that the next filter
in the filter chain will only receive complete tags.

=head1 METHOD

This class defines two methods, that are called automatically:

=over 4

=item filter()

Buffer incomplete tags to ensure that subsequent filters will only
receive complete HTML tags.

=item will_modify()

This method returns a I<false> value, thus indicating to the system
that it will not modify data passing through.

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

