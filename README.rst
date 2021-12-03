Munge Text Tools


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
              collecting = munge.parse.lookfor(lambda l: l.endswith('.'), accum, munge.space_reduce)
              continue
          yield line
      if collecting:
          yield collecting(line)

    lines = parse(strip_emptylines(by_para(replace_typography(strip_newlines(open('file'))))))
    output(lines)
