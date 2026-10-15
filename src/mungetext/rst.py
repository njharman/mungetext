"""ReStructuredText output tools."""

from functools import wraps

TITLES = ['*', '=', '-', '~']


def page(style):
    """ReST Page break."""
    return f'\n.. page:: {style}\n'


def escape_asterisk(text):
    """Asterisks are strong/emphasis in ReST."""
    return text.replace('*', r'\*')


def title(level, text):
    """ReST Title at level."""
    if level not in TITLES:
        level = TITLES[int(level)]
    return f'\n{text}\n{level * len(text)}'


def title_by_regex(lines, regexes, level):
    """ReST Title lines matching regex."""
    for line in lines:
        if [x for x in regexes if x.search(line)]:
            yield ''
            yield line
            yield level * len(line)
        else:
            yield line


def TitleByRegexFactory(regexes, level='='):
    """ReST Title."""
    try:
        iter(regexes)
    except TypeError:
        regexes = [
            regexes,
        ]

    @wraps(title_by_regex)
    def inner(lines):
        return title_by_regex(lines, regexes, level)

    return inner
