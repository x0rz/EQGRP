package HTTP::Proxy::BodyFilter::htmltext;

use strict;
use Carp;
use HTTP::Proxy::BodyFilter;
use vars qw( @ISA );
@ISA = qw( HTTP::Proxy::BodyFilter );

sub init {
    croak "Parameter must be a CODE reference" unless ref $_[1] eq 'CODE';
    $_[0]->{_filter} = $_[1];
}

sub begin { $_[0]->{js} = 0; }    # per message initialisation

sub filter {
    my ( $self, $dataref, $message, $protocol, $buffer ) = @_;

    my $pos = pos($$dataref) = 0;
  SCAN:
    {
        $pos = pos($$dataref);
        $$dataref =~ /\G<\s*(?:script|style)[^>]*>/cgi    # protect
          && do { $self->{js} = 1; redo SCAN; };
        $$dataref =~ /\G<\s*\/\s*(?:script|style)[^>]*>/cgi    # unprotect
          && do { $self->{js} = 0; redo SCAN; };
        # comments are considered as text
        # if you want comments as comments,
        # use HTTP::Proxy::BodyFilter::htmlparser
        $$dataref =~ /\G<!--/cg                  && redo SCAN;  # comment
        $$dataref =~ /\G>/cg                     && redo SCAN;  # lost >
        $$dataref =~ /\G(?=(<[^\s\/?%!a-z]))/cgi && goto TEXT;  # < in text
        $$dataref =~ /\G(?:<[^>]*>)+/cg          && redo SCAN;  # tags
        $$dataref =~ /\G(?:&[^\s;]*;?)+/cg       && redo SCAN;  # entities
        $$dataref =~ /\G([^<>&]+)/cg             && do {        # text
          TEXT:
            redo SCAN if $self->{js};    # ignore protected
            {
                local $_ = $1;
                $self->{_filter}->();
                substr( $$dataref, $pos, length($1), $_ );
                pos($$dataref) = $pos + length($_);
            }
            redo SCAN;
        };
    }
}

1;

__END__

=head1 NAME

HTTP::Proxy::BodyFilter::htmltext - A filter to transmogrify HTML text

=head1 SYNOPSIS

    use HTTP::Proxy::BodyFilter::tags;
    use HTTP::Proxy::BodyFilter::htmltext;

    # could it be any simpler?
    $proxy->push_filter(
        mime     => 'text/html',
        response => HTTP::Proxy::BodyFilter::tags->new,
        response => HTTP::Proxy::BodyFilter::htmltext->new(
            sub { tr/a-zA-z/n-za-mN-ZA-M/ }
        )
    );

=head1 DESCRIPTION

The HTTP::Proxy::BodyFilter::htmltext is a filter spawner that
calls the callback of your choice on any HTML text (outside 
C<< <script> >> and C<< <style> >> tags, and entities).

The subroutine should modify the content of C<$_> as it sees fit.
Simple, and terribly efficient.

=head1 METHODS

The filter defines the following methods, called automatically:

=over 4

=item init()

Ensures that the filter is initialised with a CODE reference.

=item begin()

Per page parser initialisation.

=item filter()

A simple HTML parser that runs the given callback on the text contained
in the HTML data. Please look at L<HTTP::Proxy::BodyFilter::htmlparser>
if you need something more elaborate.

=back

=head1 SEE ALSO

L<HTTP::Proxy>, L<HTTP::Proxy::BodyFilter>,
L<HTTP::Proxy::BodyFilter::htmlparser>.

=head1 AUTHOR

Philippe "BooK" Bruhat, E<lt>book@cpan.orgE<gt>.

=head1 COPYRIGHT

Copyright 2003-2005, Philippe Bruhat.

=head1 LICENSE

This module is free software; you can redistribute it or modify it under
the same terms as Perl itself.

=cut

