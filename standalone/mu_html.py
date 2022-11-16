from argparse import ArgumentParser
import os
import platform
from pathlib import Path
from shutil import rmtree
import requests


_BINARY_URLS = {'Linux': 'https://github.com/somik861/mu_cmake/releases/download/MU_binaries/mu_linux64_gcc8.tar.gz',
                'Windows': 'https://github.com/somik861/mu_cmake/releases/download/MU_binaries/mu_win64_cygwin.zip'}
BINARY_URL = _BINARY_URLS[platform.system()]

FILES_FOLDER_NAME = os.path.join('mu_html_files', platform.system())
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

_MU_BINARY_NAMES = {'Linux': 'mu', 'Windows': 'mu.exe'}
MU_BINARY_NAME = _MU_BINARY_NAMES[platform.system()]

_SVGTEX_BINARY_NAMES = {'Linux': 'svgtex', 'Windows': 'svgtex.exe'}
SVGTEX_BINARY_NAME = _SVGTEX_BINARY_NAMES[platform.system()]


FILES_FOLDER_PATH = Path(os.path.join(SCRIPT_FOLDER, FILES_FOLDER_NAME))
MU_BINARY_PATH = Path(os.path.join(FILES_FOLDER_PATH, MU_BINARY_NAME))
SVGTEX_BINARY_PATH = Path(os.path.join(FILES_FOLDER_PATH, SVGTEX_BINARY_NAME))


def _validate_files() -> bool:
    return True


def _clean_download() -> None:
    rmtree(FILES_FOLDER_PATH, ignore_errors=True)

    FILES_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

    data = requests.get(BINARY_URL).content

    assert _validate_files(), 'Files werent correctly downloaded,'
    'please report this at https://github.com/somik861/mu_interactive'


def init_if_needed() -> None:
    print(f'{MU_BINARY_PATH=}')
    print(f'{SVGTEX_BINARY_PATH=}')
    print(f'{SCRIPT_FOLDER=}')
    print(f'{FILES_FOLDER_PATH=}')


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
