from argparse import ArgumentParser
import os
import platform
from pathlib import Path


WINDOWS_BINARY_URL = 'https://github.com/somik861/mu_cmake/releases/download/MU_binaries/mu_win64_cygwin.zip'
LINUX_BINARY_URL = 'https://github.com/somik861/mu_cmake/releases/download/MU_binaries/mu_linux64_gcc8.tar.gz'

FILES_FOLDER_NAME = os.path.join('mu_html_files', platform.system())
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

_MU_BINARY_NAMES = {'Linux': 'mu', 'Windows': 'mu.exe'}
MU_BINARY_NAME = _MU_BINARY_NAMES[platform.system()]

_SVGTEX_BINARY_NAMES = {'Linux': 'svgtex', 'Windows': 'svgtex.exe'}
SVGTEX_BINARY_NAME = _SVGTEX_BINARY_NAMES[platform.system()]


FILES_FOLDER = os.path.join(SCRIPT_FOLDER, FILES_FOLDER_NAME)
MU_BINARY_PATH = os.path.join(FILES_FOLDER, MU_BINARY_NAME)
SVGTEX_BINARY_PATH = os.path.join(FILES_FOLDER, SVGTEX_BINARY_NAME)


def init_if_needed() -> None:
    print(f'{MU_BINARY_PATH=}')
    print(f'{SVGTEX_BINARY_PATH=}')
    print(f'{SCRIPT_FOLDER=}')
    print(f'{FILES_FOLDER=}')


def main(inp: str, out: str) -> None:
    if not out.endswith('.html'):
        out += '.html'

    init_if_needed()


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('i', metavar='IN_FILE', type=str, help='Input file')
    parser.add_argument('o', metavar='OUT_FILE', type=str, help='Output file')

    args = parser.parse_args()

    main(args.i, args.o)
