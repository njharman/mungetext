import re

import pytest

from mungetext import rst


def test_titles_constant():
    assert rst.TITLES == ['*', '=', '-', '~']


def test_page():
    assert rst.page('landscape') == '\n.. page:: landscape\n'


@pytest.mark.parametrize(
    ('text', 'expected'),
    [('a*b', r'a\*b'), ('**x**', r'\*\*x\*\*'), ('none', 'none'), ('', '')],
)
def test_escape_asterisk(text, expected):
    assert rst.escape_asterisk(text) == expected


@pytest.mark.parametrize('level', ['*', '=', '-', '~'])
def test_title_by_char(level):
    assert rst.title(level, 'Hello') == f'\nHello\n{level * 5}'


@pytest.mark.parametrize(('level', 'char'), [(0, '*'), (1, '='), (2, '-'), (3, '~'), ('2', '-')])
def test_title_by_index(level, char):
    assert rst.title(level, 'Hi') == f'\nHi\n{char * 2}'


def test_title_bad_level():
    with pytest.raises(IndexError):
        rst.title(4, 'x')
    with pytest.raises(ValueError, match='invalid literal'):
        rst.title('x', 'x')


def test_title_empty_text():
    assert rst.title('=', '') == '\n\n'


def test_title_by_regex():
    lines = ['intro', 'Chapter 1', 'body', 'chapter 2']
    regexes = [re.compile('^Chapter'), re.compile('2$')]
    assert list(rst.title_by_regex(lines, regexes, '-')) == [
        'intro',
        '',
        'Chapter 1',
        '---------',
        'body',
        '',
        'chapter 2',
        '---------',
    ]


def test_title_by_regex_matches_once_for_multiple_regexes():
    lines = ['ab']
    out = list(rst.title_by_regex(lines, [re.compile('a'), re.compile('b')], '='))
    assert out == ['', 'ab', '==']


def test_title_by_regex_no_regexes():
    assert list(rst.title_by_regex(['a'], [], '=')) == ['a']


@pytest.mark.parametrize(
    'regexes',
    [
        re.compile('^Chapter'),
        '^Chapter',
        [re.compile('^Chapter')],
        ['^Chapter'],
        ('^nomatch', re.compile('^Chapter')),
        iter(['^Chapter']),
    ],
    ids=['pattern', 'str', 'list-pattern', 'list-str', 'mixed-tuple', 'iterator'],
)
def test_title_by_regex_factory_accepts(regexes):
    func = rst.TitleByRegexFactory(regexes)
    assert list(func(['Chapter 1', 'text'])) == ['', 'Chapter 1', '=========', 'text']


def test_title_by_regex_factory_level():
    func = rst.TitleByRegexFactory('A', level='~')
    assert list(func(['A'])) == ['', 'A', '~']


def test_title_by_regex_factory_reusable():
    func = rst.TitleByRegexFactory(iter(['A']))
    assert list(func(['A'])) == list(func(['A']))


def test_title_by_regex_factory_str_not_split_into_chars():
    func = rst.TitleByRegexFactory('xy')
    assert list(func(['x', 'y'])) == ['x', 'y']


def test_title_by_regex_factory_preserves_wrapped():
    func = rst.TitleByRegexFactory('A')
    assert func.__wrapped__ is rst.title_by_regex
