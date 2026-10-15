import re

import mungetext as m


def paras(lines, **kwargs):
    return list(m.by_para(iter(lines), **kwargs))


def test_by_simple_para():
    lines = ['one', '  two  ', '', '', 'three', '']
    assert list(m.by_simple_para(lines)) == ['one two', '', 'three', '']


def test_by_simple_para_no_trailing_blank():
    assert list(m.by_simple_para(['a', 'b'])) == ['a b']


def test_by_simple_para_empty():
    assert list(m.by_simple_para([])) == []
    assert list(m.by_simple_para(['', ' '])) == []


class TestBreakBase:
    def test_blank_line_breaks_without_appending(self):
        accum = ['a']
        assert m.break_base('', accum) is True
        assert accum == ['a']

    def test_period_appends_and_breaks(self):
        accum = ['a']
        assert m.break_base('end.', accum) is True
        assert accum == ['a', 'end.']

    def test_single_colon_breaks(self):
        accum = []
        assert m.break_base('Header:', accum) is True
        assert accum == ['Header:']

    def test_multiple_colons_do_not_break(self):
        accum = []
        assert m.break_base('a: b:', accum) is None
        assert accum == []

    def test_no_break(self):
        assert m.break_base('plain text', []) is None


class TestBreakList:
    def test_breaks_before_list_header(self):
        assert m.break_list('Header:', ['previous']) == 'Header:'

    def test_empty_accum_no_break(self):
        assert m.break_list('Header:', []) is None

    def test_lowercase_no_break(self):
        assert m.break_list('header:', ['previous']) is None

    def test_multiple_colons_no_break(self):
        assert m.break_list('Time: 10:', ['previous']) is None

    def test_no_trailing_colon_no_break(self):
        assert m.break_list('Header', ['previous']) is None


class TestBreakRegexFactory:
    def test_match_appends_and_breaks(self):
        func = m.break_regex_factory(r'^\d+\)')
        accum = ['a']
        assert func('1) item', accum) is True
        assert accum == ['a', '1) item']

    def test_match_newline_returns_line(self):
        func = m.break_regex_factory(r'^\d+\)', newline=True)
        accum = ['a']
        assert func('1) item', accum) == '1) item'
        assert accum == ['a']

    def test_no_match(self):
        func = m.break_regex_factory(r'^\d+\)')
        accum = []
        assert func('text', accum) is None
        assert accum == []

    def test_empty_line_match_breaks_without_append(self):
        func = m.break_regex_factory(r'^$')
        accum = ['a']
        assert func('', accum) is True
        assert accum == ['a']

    def test_search_not_match(self):
        func = m.break_regex_factory('mid')
        assert func('a mid b', []) is True


class TestByPara:
    def test_blank_lines_split(self):
        assert paras(['one', 'two', '', 'three']) == ['one two', 'three']

    def test_period_ends_paragraph(self):
        assert paras(['One.', 'Two', 'three.']) == ['One.', 'Two three.']

    def test_colon_ends_paragraph(self):
        assert paras(['intro:', 'item']) == ['intro:', 'item']

    def test_multiple_colons_do_not_split(self):
        assert paras(['a: b:', 'c']) == ['a: b: c']

    def test_list_header_ends_paragraph_by_default(self):
        # break_base fires first on a lone-colon line, so break_list is never reached with default breaks.
        assert paras(['some text', 'Header:', 'item one', 'item two.']) == [
            'some text Header:',
            'item one item two.',
        ]

    def test_list_header_gets_own_line_with_override(self):
        assert paras(['some text', 'Header:', 'x'], override=[m.break_list]) == ['some text', 'Header: x']

    def test_dehyphenates(self):
        assert paras(['hyphen-', 'ated word.']) == ['hyphenated word.']

    def test_never_yields_empty(self):
        assert paras(['', '', 'a.', '', '', 'b']) == ['a.', 'b']
        assert paras([]) == []
        assert paras(['', '']) == []

    def test_rest_title(self):
        assert paras(['Title', '=====', 'Body text.']) == ['<title>Title\n=====', 'Body text.']

    def test_title_underline_length_must_match(self):
        assert paras(['Title', '==', 'x']) == ['Title == x']

    def test_title_requires_single_preceding_line(self):
        assert paras(['one', 'two', '===']) == ['one two', '<table>===']

    def test_table(self):
        lines = ['before', '===  ===', 'a    b', '===  ===', '1    2', '===  ===', 'after.']
        assert paras(lines) == [
            'before',
            '<table>===  ===\na    b\n===  ===\n1    2\n===  ===',
            'after.',
        ]

    def test_table_at_start_has_no_empty_paragraph(self):
        lines = ['===  ===', 'a    b', '===  ===', '1    2', '===  ===']
        assert paras(lines) == ['<table>===  ===\na    b\n===  ===\n1    2\n===  ===']

    def test_table_rows_are_rstripped(self):
        lines = ['===  ===  ', 'a    b   ', '===  ===', '1    2', '===  ===']
        assert paras(lines)[0].startswith('<table>===  ===\na    b\n')

    def test_directive_with_body(self):
        lines = ['intro', '.. note::', '   body', '', '   more', 'after.']
        assert paras(lines) == ['intro', '<order>.. note::\n   body\n\n   more', 'after.']

    def test_directive_at_start(self):
        assert paras(['.. page:: x', 'text.']) == ['<order>.. page:: x', 'text.']

    def test_directive_at_end_of_input(self):
        assert paras(['text.', '.. note::', '   body']) == ['text.', '<order>.. note::\n   body']

    def test_directive_ended_by_blank_then_text(self):
        assert paras(['.. note::', '   body', '', 'next']) == ['<order>.. note::\n   body', 'next']

    def test_consecutive_directives(self):
        assert paras(['.. a::', '.. b::']) == ['<order>.. a::', '<order>.. b::']

    def test_directive_flushes_dehyphenated_paragraph(self):
        assert paras(['hyphen-', 'ated', '.. a::']) == ['hyphenated', '<order>.. a::']

    def test_extra_tests_break(self):
        def break_digit(line, accum):
            if line[:1].isdigit():
                return line

        assert paras(['intro', '1 one', '2 two'], tests=[break_digit]) == ['intro', '1 one', '2 two']

    def test_extra_tests_run_before_base(self):
        calls = []

        def spy(line, accum):
            calls.append(line)

        assert paras(['a.', 'b'], tests=[spy]) == ['a.', 'b']
        assert calls == ['a.', 'b']

    def test_override_replaces_base_breaks(self):
        # Without break_base, blank lines and periods no longer split.
        assert paras(['one.', '', 'two'], override=[lambda line, accum: False]) == ['one.  two']

    def test_override_break(self):
        assert paras(['a', 'STOP', 'b'], override=[lambda line, accum: line == 'STOP']) == ['a', 'b']

    def test_regex_break_integration(self):
        func = m.break_regex_factory(r'^\d+\)', newline=True)
        assert paras(['1) a', 'cont', '2) b'], tests=[func]) == ['1) a cont', '2) b']
        assert re.match(r'^\d', '1')
