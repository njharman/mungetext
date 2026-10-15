"""Output functions."""

import textwrap

indenter = textwrap.TextWrapper(subsequent_indent='  ').fill


def parapper(text):
    """Wrap lines into paragraphs."""
    # Return text with embeded newlines unchanged.
    if '\n' in text:
        return text
    return textwrap.TextWrapper().fill(text)


def doublespace(seq):
    """Output blank line separated."""
    return '\n\n'.join(seq)
