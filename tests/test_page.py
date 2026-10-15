import mungetext as m


def pages(lines):
    return list(m.by_page(iter(lines)))


class TestByPage:
    def test_splits_and_removes_footer(self):
        lines = ['a1', 'a2', 'footer 1', '\fb1', 'b2', 'footer 2', '\fc1']
        assert pages(lines) == [['a1', 'a2'], ['b1', 'b2'], ['c1']]

    def test_text_after_page_break_is_kept(self):
        assert pages(['a', 'footer', '\fChapter 2', 'b']) == [['a'], ['Chapter 2', 'b']]

    def test_break_only_line(self):
        assert pages(['a', 'footer', '\f', 'b']) == [['a'], ['b']]

    def test_text_before_break_is_end_of_page(self):
        assert pages(['a', 'b', 'c\fd']) == [['a', 'b'], ['d']]

    def test_break_on_first_line_does_not_crash(self):
        assert pages(['\f', 'a']) == [['a']]

    def test_single_line_page_is_all_footer(self):
        assert pages(['footer', '\f', 'a']) == [['a']]

    def test_consecutive_breaks(self):
        assert pages(['a', 'footer', '\f', '\f', 'b']) == [['a'], ['b']]

    def test_no_break_one_page(self):
        assert pages(['a', 'b']) == [['a', 'b']]

    def test_empty(self):
        assert pages([]) == []

    def test_trailing_break_no_empty_page(self):
        assert pages(['a', 'footer', '\f']) == [['a']]


class TestTwoColumnPage:
    def test_single_column_unchanged(self):
        page = ['one', 'two', '']
        assert m.twocolumn_page_to_onecolumn_lines(page) == page

    def test_two_columns(self):
        page = ['left1    right1', 'left2    right2']
        assert m.twocolumn_page_to_onecolumn_lines(page) == ['left1    ', 'left2    ', 'right1', 'right2']

    def test_blank_lines_go_to_first_column(self):
        page = ['left1    right1', '', 'left2    right2']
        assert m.twocolumn_page_to_onecolumn_lines(page) == ['left1    ', '', 'left2    ', 'right1', 'right2']

    def test_mixed_full_width_and_columns(self):
        page = ['Heading', 'left1    right1']
        assert m.twocolumn_page_to_onecolumn_lines(page) == ['Heading', 'left1    ', 'right1']

    def test_short_second_column_is_not_split_cleanly(self):
        # Scan stops len(line) - 3 short, so second columns under 4 chars keep leading spaces.
        assert m.twocolumn_page_to_onecolumn_lines(['l1    r1']) == ['l1  ', '  r1']

    def test_paragraph_indent_plus_three(self):
        # winnar column is 10 (most common). Row with second column at 13 has leading indent kept.
        page = ['aaaaaa    bbbb', 'cccccc    dddd', 'eeeeee       ffff']
        one_col = m.twocolumn_page_to_onecolumn_lines(page)
        assert one_col[3:] == ['bbbb', 'dddd', '   ffff']

    def test_paragraph_indent_plus_two(self):
        page = ['aaaaaa    bbbb', 'cccccc    dddd', 'eeeeee      ffff']
        one_col = m.twocolumn_page_to_onecolumn_lines(page)
        assert one_col[3:] == ['bbbb', 'dddd', '  ffff']

    def test_empty_page(self):
        assert m.twocolumn_page_to_onecolumn_lines([]) == []

    def test_only_blank_lines(self):
        assert m.twocolumn_page_to_onecolumn_lines(['', '  ']) == ['', '  ']

    def test_ties_go_to_last_seen(self):
        # Second columns start at 10 and 12, one vote each; 12 wins, so the col-12 row is not indent-trimmed.
        page = ['aaaaaa    bbbb', 'cccccc      dddd']
        assert m.twocolumn_page_to_onecolumn_lines(page) == ['aaaaaa    ', 'cccccc      ', 'bbbb', 'dddd']


def test_detwocolumn():
    lines = ['left1    right1', 'footer', '\fleft2    right2', 'footer', '\f']
    assert list(m.detwocolumn(lines)) == ['left1    ', 'right1', 'left2    ', 'right2']
