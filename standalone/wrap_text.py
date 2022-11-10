from argparse import ArgumentParser
from typing import Generator


def _blocks(lines: list[str]) -> Generator[list[str], None, None]:
    buffer: list[str] = []
    for line in lines:
        if line == '\n':
            if buffer:
                yield buffer
            buffer = []
            continue
        buffer.append(line)

    if buffer:
        yield buffer


def _ignore_block(block: list[str]) -> bool:
    if block and block[0][0] == '\t':
        return True

    return False


def _lines(string: str, width: int) -> Generator[str, None, None]:
    words = string.split()
    buffer = ''
    for word in words:
        if len(word) + len(buffer) + 2 >= width:
            yield buffer.strip() + '\n'
            buffer = ''

        buffer += word + ' '

    if buffer:
        yield buffer.strip() + '\n'


def _wrap_block(block: list[str], width: int) -> list[str]:
    flat = ''.join(block).replace('\n', ' ')
    while '  ' in flat:
        flat.replace('  ', ' ')

    return [line for line in _lines(flat, width)]


def wrap_text(input_lines: list[str], width: int) -> list[str]:
    out: list[str] = []
    for block in _blocks(input_lines):
        if _ignore_block(block):
            out.extend(block + ['\n'])
            continue
        out.extend(_wrap_block(block, width) + ['\n'])

    return out


if __name__ == '__main__':
    parser = ArgumentParser('py wrap_text.py')

    parser.add_argument('infile', metavar='IN_FILE', type=str)
    parser.add_argument('-o', required=False, metavar='OUT_FILE', type=str)
    parser.add_argument('-i', required=False, action='store_true')
    parser.add_argument('-w', required=False,
                        metavar='WRAP', type=int, default=80)

    args = parser.parse_args()

    new_lines = wrap_text(open(args.infile).readlines(), args.w)

    if args.o is None and not args.i:
        for line in new_lines:
            print(line, end='')

    if args.i:
        open(args.infile, 'w').writelines(new_lines)

    if args.o is not None:
        open(args.o, 'w').writelines(new_lines)
