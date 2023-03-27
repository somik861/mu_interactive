from argparse import ArgumentParser
from pathlib import Path
from typing import Generator
import re

IGNORE_INDENT = ['\t', ' ' * 4]
PREVENT_SPLIT = [('‹', '›'), ('«', '»')]

_ARG_INPUT: Path = Path()
_ARG_OUTPUT: str = 'stdout'
_ARG_ROW_LIMIT: int = 80
_ARG_INPLACE: bool = False


def _blocks(lines: list[str]) -> Generator[list[str], None, None]:
    """return blocks that might be wrap, block are non-empty lists of lines"""
    buffer: list[str] = []

    for line in lines:
        # end of text block
        if line == '\n' or any(line.startswith(x) for x in IGNORE_INDENT):
            if buffer:
                yield buffer
            yield [line]
            buffer = []

        buffer.append(line)

    if buffer:
        yield buffer


def _lines(flat_block: str) -> Generator[str, None, None]:
    def replace(match: re.Match) -> str:
        return match.group(0).replace(' ', '\x00')

    for start, end in PREVENT_SPLIT:
        flat_block = re.sub(f'{start}[^{end}]*{end}', replace, flat_block)

    words = flat_block.split(' ')

    buffer = ''
    for word in words:
        if len(word) + len(buffer) + 1 > _ARG_ROW_LIMIT:  # (+ 1) => newline
            yield buffer.strip() + '\n'
            buffer = ''

        buffer += word + ' '

    if buffer:
        yield buffer.strip() + '\n'


def _ignore_block(block: list[str]) -> bool:
    return block == ['\n'] or any(block[0].startswith(x) for x in IGNORE_INDENT)


def _wrap_block(block: list[str]) -> list[str]:
    flat = ''.join(block).replace('\n', ' ')
    while ' ' * 2 in flat:
        flat = flat.replace(' ' * 2, ' ')

    return [line for line in _lines(flat)]


def main() -> None:
    input_lines = open(_ARG_INPUT, 'r', encoding='utf-8').readlines()

    out_lines = []
    for block in _blocks(input_lines):
        if _ignore_block(block):
            out_lines.extend(block)
            continue

        out_lines.extend(_wrap_block(block))

    if _ARG_INPLACE:
        open(
            _ARG_INPUT,
            'w',
            newline='\n',
            encoding='utf-8',
        ).writelines(out_lines)
        return

    if _ARG_OUTPUT == 'stdout':
        for line in out_lines:
            print(line, end='')
    else:
        open(
            _ARG_OUTPUT,
            'w',
            newline='\n',
            encoding='utf-8',
        ).writelines(out_lines)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(
        'input',
        metavar='INPUT',
        type=Path,
        help='Input file',
    )

    parser.add_argument(
        '--output',
        '-o',
        metavar='OUT',
        type=str,
        default=_ARG_OUTPUT,
        help=f'Output location; path to a file or \'stdout\'; default=\'{_ARG_OUTPUT}\'',
    )

    parser.add_argument(
        '--row_limit',
        '-l',
        metavar='N',
        type=int,
        default=_ARG_ROW_LIMIT,
        help=f'Row limit size in characters; default={_ARG_ROW_LIMIT}',
    )

    parser.add_argument(
        '--inplace',
        '-i',
        action='store_true',
        help='Make changes in-place; disables \'output\' option',
    )

    args = parser.parse_args()

    _ARG_INPUT = args.input
    _ARG_OUTPUT = args.output
    _ARG_ROW_LIMIT = args.row_limit
    _ARG_INPLACE = args.inplace

    main()
