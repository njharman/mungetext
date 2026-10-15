import re

import pytest

import mungetext as m


def lines_of(func, lines, *args, **kwargs):
    return list(func(iter(lines), *args, **kwargs))


def test_version():
    assert m.__version__ == '0.0.1'


def test_alpha_sort_numbers_numerically():
    assert sorted(['a10', 'a2', 'a1', 'b1'], key=m.alpha_sort) == ['a1', 'a2', 'a10', 'b1']


def test_match_any_returns_first_match():
    regexes = [re.compile('x'), re.compile('a(b)'), re.compile('ab')]
    match = m.match_any('abc', regexes)
    assert match.group(1) == 'b'


def test_match_any_no_match():
    assert m.match_any('abc', [re.compile('x')]) is None
    assert m.match_any('abc', []) is None


def test_slurp_re_collects_until_stop():
    lines = ['Key: one', '  two ', 'three', 'STOP', 'other']
    assert m.slurp_re(re.compile('STOP'), 0, lines, ':') == (2, 'one two three')


def test_slurp_re_strip_uses_last_partition():
    lines = ['a: b: c', 'STOP']
    assert m.slurp_re(re.compile('STOP'), 0, lines, ':') == (0, 'c')


def test_slurp_re_strip_missing_keeps_whole_line():
    assert m.slurp_re(re.compile('STOP'), 0, ['  hello ', 'STOP'], ':') == (0, 'hello')


def test_slurp_re_runs_to_end_without_match():
    assert m.slurp_re(re.compile('STOP'), 0, ['a', 'b', 'c'], ':') == (2, 'a b c')


def test_slurp_re_single_line():
    assert m.slurp_re(re.compile('x'), 0, ['only'], ':') == (0, 'only')


def test_lookfor_accumulates_until_test_true():
    accum = []
    finder = m.lookfor(lambda line: line.endswith('.'), accum, m.space_reduce)
    assert list(finder('one')) == []
    assert list(finder('two')) == []
    assert list(finder('three.')) == ['one two three.']
    assert accum == ['one', 'two', 'three.']


@pytest.mark.parametrize(('char', 'expected'), [('A', True), ('a', False), ('1', True), ('', True), (' ', True)])
def test_is_cap(char, expected):
    assert m.is_cap(char) is expected


def test_space_reduce():
    assert list(m.space_reduce(['a', 'b'])) == ['a b']


def test_joinlines_continuation():
    lines = ['1 first', 'cont', '2 second', '3 third', 'more', 'evenmore']
    result = lines_of(m.joinlines, lines, lambda line: line[0].isdigit())
    assert result == ['1 first cont', '2 second', '3 third more evenmore']


def test_joinlines_separator():
    result = lines_of(m.joinlines, ['A', 'b', 'C'], str.isupper, separator='|')
    assert result == ['A|b', 'C']


def test_joinlines_leading_continuation_lines_kept():
    assert lines_of(m.joinlines, ['x', 'y', 'Z'], str.isupper) == ['x y', 'Z']


def test_joinlines_empty():
    assert lines_of(m.joinlines, [], bool) == []


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ('“quoted”', '"quoted"'),
        ('a—b', 'a--b'),
        ('it\u2019s', "it's"),
        ('\xc2\x92', "'"),
        ('\xc2\x93x\xc2\x94', '"x"'),
        ('\xe2\x80\x93', '-'),
        ('plain', 'plain'),
        ('', ''),
    ],
)
def test_replace_typography(raw, expected):
    assert lines_of(m.replace_typography, [raw]) == [expected]


def test_strip_newlines_default():
    assert lines_of(m.strip_newlines, ['a\n', '\nb\n\n', 'c']) == ['a', 'b', 'c']


def test_strip_newlines_keeps_other_whitespace():
    assert lines_of(m.strip_newlines, [' a \n']) == [' a ']


def test_strip_newlines_custom_char():
    assert lines_of(m.strip_newlines, ['--a--'], strip='-') == ['a']


def test_strip_emptylines():
    assert lines_of(m.strip_emptylines, ['a', '', '  ', '\t', ' b ']) == ['a', ' b ']


def test_strip_commentlines():
    lines = ['keep', '# gone', '   # gone too', 'keep # inline', '']
    assert lines_of(m.strip_commentlines, lines) == ['keep', 'keep # inline', '']


def test_strip_commentlines_custom_char():
    assert lines_of(m.strip_commentlines, ['; no', '# yes'], char=';') == ['# yes']


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ('code # comment', 'code '),
        ('code # a # b', 'code '),
        ('# all', ''),
        ('no comment', 'no comment'),
        ('', ''),
    ],
)
def test_strip_comments(raw, expected):
    assert lines_of(m.strip_comments, [raw]) == [expected]


def test_strip_comments_char_is_literal():
    assert lines_of(m.strip_comments, ['a.b.c', 'abc'], char='.') == ['a', 'abc']
    assert lines_of(m.strip_comments, ['a*b'], char='*') == ['a']


def test_strip_default_whitespace():
    assert lines_of(m.strip, ['  a  ', '\tb\n']) == ['a', 'b']


def test_strip_char():
    assert lines_of(m.strip, ['--a--', ' a '], char='-') == ['a', ' a ']


@pytest.mark.parametrize(
    ('lines', 'expected'),
    [
        (['hyphen-', 'ated'], ['hyphenated']),
        (['hyphen-  ', '  ated rest'], ['hyphenated rest']),
        (['a-', 'b-', 'c'], ['abc']),
        (['dash--', 'next'], ['dash--', 'next']),
        (['-', 'next'], ['-', 'next']),
        (['plain ', 'lines'], ['plain', 'lines']),
        (['trailing-'], ['trailing']),
        ([], []),
    ],
)
def test_dehyphenate(lines, expected):
    assert lines_of(m.dehyphenate, lines) == expected
