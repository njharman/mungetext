"""Parse and reformat PDF's converted to text."""

import re
from collections import defaultdict

from . import out, rst

__version__ = '0.0.1'

PAGE_BREAK = '\f'

RE_EMPTYLINE = re.compile(r'^\s*$')

# Sort alphabetically 10 after 2,4,8,etc.
alpha_sort = lambda key: [int(t) if t.isdigit() else t for t in re.split('([0-9]+)', key)]


def match_any(line, regexes):
    """Return first regex that matches line or None."""
    for regex in regexes:
        if match := regex.match(line):
            return match


def slurp_re(stopon, i, lines, strip):
    """Slurp lines until line matches re 'stopon'."""
    bits = list()
    bits.append(lines[i].rpartition(strip)[2].strip())
    while i + 1 < len(lines) and not stopon.match(lines[i + 1]):
        i += 1
        bits.append(lines[i].strip())
    return i, ' '.join(bits).strip()


def lookfor(test, accum, reduce):
    """TBD."""

    def finder(line):
        accum.append(line)
        if test(line):
            yield from reduce(accum)

    return finder


# Lookfor tests.


def is_cap(char):
    """Func lookfor test."""
    return char == char.upper()


def space_reduce(lines):
    """Func lookfor reducer."""
    yield ' '.join(lines)


# Line Oriented.


def joinlines(lines, start, separator=' '):
    """Join continuation lines into one line.

    start(line) returns True if line is start of new line.
    Else line is concatenated to previous line.

    concatenated lines are joined by separator.
    """
    accum = list()
    for line in lines:
        if start(line):
            if accum:
                yield separator.join(accum)
            accum = list()
        accum.append(line)
    # Last one.
    if accum:
        yield separator.join(accum)


def replace_typography(lines):
    """Replace weirdo characters."""
    for line in lines:
        yield (
            line.replace('“', '"')
            .replace('”', '"')
            .replace('—', '--')
            .replace('\u2019', "'")
            .replace('\xc2\x92', "'")
            .replace('\xc2\x93', '"')
            .replace('\xc2\x94', '"')
            .replace('\xe2\x80\x93', '-')
        )


def strip_newlines(lines, strip='\n'):
    """Remove newlines from end of lines."""
    for line in lines:
        yield line.strip(strip)


def strip_emptylines(lines):
    """Remove lines containing only whitespace."""
    for line in lines:
        if line.strip():
            yield line


def strip_commentlines(lines, char='#'):
    """Remove lines starting with char or whitespace and then char."""
    for line in lines:
        if not line.lstrip().startswith(char):
            yield line


def strip_comments(lines, char='#'):
    """Remove from comment character to end of line."""
    for line in lines:
        yield line.partition(char)[0]


def strip(lines, char=None):
    if char:
        args = (char,)
    else:
        args = ()
    for line in lines:
        yield line.strip(*args)


def dehyphenate(lines):
    """Combine two lines with hyphenated word into one line, removing hyphen."""
    first = ''
    for raw in lines:
        line = raw.rstrip()
        if len(line) > 1 and line[-1] == '-' and line[-2] != '-':
            first += line[:-1]
            continue
        if first:
            yield first + line.lstrip()
            first = ''
        else:
            yield line
    if first:
        yield first


def by_simple_para(lines):
    """Combine multiple lines into one line, delineated by blank lines."""
    para = list()
    for line in lines:
        if line.strip():
            para.append(line.strip())
        elif para:
            yield ' '.join(para)
            yield ''
            para = list()
    if para:
        yield ' '.join(para)


def by_para(lines, tests=(), override=()):
    """Splits into paragraphs.

    Splits on
      - blank lines
      - lines ending with .
      - lines ending with : (if only one colon on line)

    Dehyphenates.
    Understand ReST orders, titles and tables. marks them with <order>, <title> <table>.

    :param tests: break when func(line, accum) returns True
    :param override: break when func(line, accum) returns True
    :return: single line (with possible newlines embedded (for tables))
    """
    breakfuncs = list(override)
    breakfuncs.extend(list(tests))
    if not override:
        breakfuncs.append(break_base)
        breakfuncs.append(break_list)
    in_table = 0
    in_order = 0
    accumulate = list()
    for raw in lines:
        line = raw
        # ReST directive. Must be first, sucks all lines until unindent.
        if line.startswith('.. '):
            if accumulate:
                yield ' '.join(dehyphenate(accumulate))
            accumulate = ['<order>' + line]
            in_order = True
            continue
        if in_order:
            if line.startswith(' ') or not line:
                accumulate.append(line)
                continue
            in_order = False
            yield '\n'.join(accumulate).rstrip()
            accumulate = list()
        # ReST title
        if line and line[0] in rst.TITLES and len(accumulate) == 1 and len(accumulate[0]) == len(line):
            yield f'<title>{accumulate[0]}\n{line}'
            accumulate = list()
            continue
        # ReST table
        if line.startswith('==='):
            if in_table == 0:  # End previous para, start table.
                if accumulate:
                    yield ' '.join(dehyphenate(accumulate))
                line = '<table>' + line
                accumulate = list()
            if in_table < 2:  # Tables, have three === separator lines.
                in_table += 1
            else:  # End table.
                in_table = 0
                accumulate.append(line.rstrip())
                yield '\n'.join(accumulate)
                accumulate = list()
                continue
        if in_table:
            accumulate.append(line.rstrip())
            continue
        for test in breakfuncs:
            foo = test(line, accumulate)
            if foo:
                if text := ' '.join(dehyphenate(accumulate)):
                    yield text
                accumulate = list()
                if foo is not True:
                    accumulate.append(foo)
                break
        else:
            accumulate.append(line)
    if in_order:
        yield '\n'.join(accumulate).rstrip()
    elif accumulate:
        yield ' '.join(dehyphenate(accumulate))


def break_base(line, accum):
    """Break on blank line or after line ending with period or colon (if only colon on line)."""
    if not line or line.endswith('.') or (line.endswith(':') and line.count(':') == 1):
        if line:
            accum.append(line)
        return True


def break_list(line, accum):
    """Break before "List Header:" should be on its own line."""
    if accum and line.endswith(':') and line.count(':') == 1 and is_cap(line[0]):
        return line


def break_regex_factory(regex, newline=False):
    """TBD."""

    def break_regex(line, accum):
        # Break when regex matches
        if matcher.search(line):
            if line and newline:
                return line
            if line:
                accum.append(line)
            return True

    matcher = re.compile(regex)
    return break_regex


# Page Oriented


def detwocolumn(lines):
    """Convert twocolumn (from PDF) to one."""
    for page in by_page(lines):
        yield from twocolumn_page_to_onecolumn_lines(page)


def by_page(lines):
    """Split into groups of lines by PAGE_BREAK. Remove page break, page numbers, etc."""
    page = list()
    for line in lines:
        if PAGE_BREAK in line:
            before, _, after = line.partition(PAGE_BREAK)
            if before.strip():
                page.append(before)
            if page:
                page.pop()  # The pagenumber/footer
            if page:
                yield page
            # Text following the break (pdftotext puts it at the start of the next page) is kept.
            page = [after] if after.strip() else list()
        else:
            page.append(line)
    if page:
        yield page


def twocolumn_page_to_onecolumn_lines(page):
    """Convert one "page" of pdftotext 2 column output to list of 1 column lines."""
    # Find the most common start column.
    lengths = defaultdict(int)
    for line in page:
        if not line.strip():
            continue
        found_three = False
        for halfsie in range(max(0, len(line) - 3)):
            if line[halfsie : halfsie + 4] == '    ':
                found_three = True
            if not found_three:
                continue
            if line[halfsie] != ' ':
                break
        if not found_three:
            continue
        lengths[halfsie] += 1
    if lengths:
        winnar = max(reversed(lengths.items()), key=lambda x: x[1])[0]  # Ties go to the last seen.
    else:
        winnar = 0
    one = list()
    two = list()
    for line in page:
        if not line.strip():
            one.append(line)
            continue
        # Find column of first non space after three spaces.
        found_three = False
        for halfsie in range(max(0, len(line) - 3)):
            if line[halfsie : halfsie + 4] == '    ':
                found_three = True
            if not found_three:
                continue
            if line[halfsie] != ' ':
                break
        if not found_three:
            one.append(line)
        else:
            one.append(line[:halfsie])
            # If second column is winnar+3 or winnar+2 assume it's paragraph leading indent.
            if halfsie == winnar + 3 and line[halfsie - 3 : halfsie] == '   ':
                two.append(line[halfsie - 3 :])
            elif halfsie == winnar + 2 and line[halfsie - 2 : halfsie] == '  ':
                two.append(line[halfsie - 2 :])
            else:
                two.append(line[halfsie:])
    return one + two
