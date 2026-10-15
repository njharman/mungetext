Munge Text Tools
================

Generator-based tools to parse and reformat PDFs converted to text (e.g. by ``pdftotext``) into ReStructuredText.

Install::

  uv add git+https://github.com/njharman/mungetext


Example::

  def parse(lines):
      collecting = False
      redo = False
      while True:
          if not redo:
              line = next(lines)
          redo = False
          if collecting:
              for stuff in collecting(line):
                  if not stuff:
                      break
                  yield stuff
              else:
                  collecting = False
              continue
          if line.startswith('Burial Alcoves:'):
              accum = list()
              if 'Contents:' in line:
                  redo = True
              else:
                  accum.append(line)
              collecting = mungetext.lookfor(lambda l: l.endswith('.'), accum, mungetext.space_reduce)
              continue
          yield line
      if collecting:
          yield collecting(line)

    lines = parse(mungetext.strip_emptylines(mungetext.by_para(mungetext.replace_typography(mungetext.strip_newlines(open('file'))))))
    print(*lines, sep='\n')

License
-------

MIT, see ``LICENSE``.
