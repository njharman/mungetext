import textwrap

import pytest

from mungetext import out


def test_parapper_wraps_at_70():
    text = ' '.join(['word'] * 30)
    result = out.parapper(text)
    assert result == textwrap.fill(text)
    assert all(len(x) <= 70 for x in result.split('\n'))
    assert '\n' in result


def test_parapper_short_text_unchanged():
    assert out.parapper('short text') == 'short text'


def test_parapper_embedded_newline_unchanged():
    text = 'table\n===  ===\n' + 'x ' * 100
    assert out.parapper(text) == text


def test_parapper_empty():
    assert out.parapper('') == ''


def test_indenter_subsequent_indent():
    text = ' '.join(['word'] * 30)
    first, *rest = out.indenter(text).split('\n')
    assert not first.startswith(' ')
    assert rest
    assert all(x.startswith('  ') and not x.startswith('   ') for x in rest)


@pytest.mark.parametrize(
    ('seq', 'expected'),
    [
        (['a', 'b', 'c'], 'a\n\nb\n\nc'),
        (['only'], 'only'),
        ([], ''),
        (iter(['a', 'b']), 'a\n\nb'),
        (['a', '', 'b'], 'a\n\n\n\nb'),
    ],
)
def test_doublespace(seq, expected):
    assert out.doublespace(seq) == expected
