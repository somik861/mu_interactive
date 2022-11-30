from argparse import ArgumentParser
import os
import platform
from pathlib import Path
from shutil import rmtree, unpack_archive
from typing import Any
import requests
import json
import subprocess
import re

HEADER = {'title': 'Generic title',
          'authors': 'Generic author',
          'doctype': 'lnotes',
          'typing': 'plain'}

_BINARY_URLS = {'Linux': 'https://github.com/somik861/mu_cmake/releases/download/v0.0.2-pre/linux64_gcc8.tar.gz',
                'Windows': 'https://github.com/somik861/mu_cmake/releases/download/v0.0.2-pre/win64_cygwin.zip'}
BINARY_URL = _BINARY_URLS[platform.system()]

FILES_FOLDER_NAME = os.path.join('mu_html_files', platform.system())
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

_MU_BINARY_NAMES = {'Linux': 'mu',
                    'Windows': os.path.join('cygwin64', 'bin', 'mu.exe')}
MU_BINARY_NAME = _MU_BINARY_NAMES[platform.system()]

_SVGTEX_BINARY_NAMES = {'Linux': 'svgtex',
                        'Windows': os.path.join('cygwin64', 'bin', 'svgtex.exe')}
SVGTEX_BINARY_NAME = _SVGTEX_BINARY_NAMES[platform.system()]


FILES_FOLDER_PATH = Path(os.path.join(SCRIPT_FOLDER, FILES_FOLDER_NAME))
MU_BINARY_PATH = Path(os.path.join(FILES_FOLDER_PATH, MU_BINARY_NAME))
SVGTEX_BINARY_PATH = Path(os.path.join(FILES_FOLDER_PATH, SVGTEX_BINARY_NAME))
CONFIG_PATH = Path(os.path.join(FILES_FOLDER_PATH, 'config.json'))

_HTML_PATHS = {'Linux': 'html',
               'Windows': os.path.join('cygwin64', 'bin', 'html')}
HTML_PATH = Path(os.path.join(FILES_FOLDER_PATH,
                 _HTML_PATHS[platform.system()]))

_TEX_PATHS = {'Linux': 'tex', 'Windows': os.path.join(
    'cygwin64', 'bin', 'tex')}
TEX_PATH = Path(os.path.join(FILES_FOLDER_PATH, _TEX_PATHS[platform.system()]))

_FONTS_PATHS = {'Linux': 'fonts',
                'Windows': os.path.join('cygwin64', 'bin', 'fonts')}
FONTS_PATH = Path(os.path.join(FILES_FOLDER_PATH,
                  _FONTS_PATHS[platform.system()]))


class utils:
    @staticmethod
    def get_url_filename(url: str) -> str:
        return url.rsplit('/', 1)[-1]

    @staticmethod
    def load_config() -> dict[str, Any]:
        return json.load(open(CONFIG_PATH, 'r'))  # type: ignore

    @staticmethod
    def save_config(cfg: dict[str, Any]) -> None:
        json.dump(cfg, open(CONFIG_PATH, 'w'), indent=4)


def _validate_files() -> bool:
    try:
        assert FILES_FOLDER_PATH.exists()
        assert MU_BINARY_PATH.exists()
        assert SVGTEX_BINARY_PATH.exists()
        assert CONFIG_PATH.exists()
        assert HTML_PATH.exists()
        assert TEX_PATH.exists()
        assert FONTS_PATH.exists()

        cfg = utils.load_config()
        assert 'version' in cfg
        assert cfg['version'] == BINARY_URL or cfg['version'] == 'custom'
    except AssertionError:
        return False

    return True


def _clean_download() -> None:
    print('Removing old files...')
    rmtree(FILES_FOLDER_PATH, ignore_errors=True)

    FILES_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

    print('Downloading binaries...')
    filepath = os.path.join(
        FILES_FOLDER_PATH, utils.get_url_filename(BINARY_URL))
    data = requests.get(BINARY_URL).content

    assert data != b'Not Found', 'Cannot download requested file, ' + \
        'please check your connection or report issue at https://github.com/somik861/mu_interactive'

    open(filepath, mode='wb').write(data)

    print('Unpacking data...')
    unpack_archive(filepath, extract_dir=FILES_FOLDER_PATH)

    cfg: dict[str, Any] = {}
    cfg['version'] = BINARY_URL
    utils.save_config(cfg)

    print('Cleaning temporary files...')
    Path(filepath).unlink()

    assert _validate_files(), 'Files werent correctly downloaded,' + \
        'please report this at https://github.com/somik861/mu_interactive'


def init_if_needed() -> None:
    if not _validate_files():
        _clean_download()


def _complete_header(source: str) -> str:
    splitted = source.splitlines()
    found: set[str] = set()

    for line in splitted:
        if line.strip() == '':
            break

        if re.match(r'\s*:.*:', line) is None:
            break

        found.add(line.split(':')[1])

    to_prepend = ''

    for key, value in HEADER.items():
        if key in found:
            continue

        to_prepend += f': {key} : {value}\n'

    return to_prepend + source


def get_html(source: str) -> str:
    result = subprocess.run([MU_BINARY_PATH, '--html', '--embed', HTML_PATH],
                            input=source.encode(encoding='utf-8'), capture_output=True)

    tex_cache = Path(os.path.join(FILES_FOLDER_PATH, 'texmf_cache'))
    tex_cache.mkdir(parents=True, exist_ok=True)

    os.putenv('TEXINPUTS', str(TEX_PATH))
    os.putenv('OSFONTDIR', str(FONTS_PATH))
    os.putenv('TEXMFCACHE', str(tex_cache))

    result = subprocess.run([SVGTEX_BINARY_PATH],
                            input=result.stdout, capture_output=True)

    return result.stdout.decode(encoding='utf-8')


def main(inp: str, out: str, complete_header: bool = True) -> None:
    if not out.endswith('.html'):
        out += '.html'

    init_if_needed()

    source = open(inp, 'r', encoding='utf-8').read()

    if complete_header:
        source = _complete_header(source)
    html = get_html(source)
    open(out, 'w', encoding='utf-8').write(html)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('i', metavar='IN_FILE', type=str, help='Input file')
    parser.add_argument('o', metavar='OUT_FILE', type=str, help='Output file')
    parser.add_argument('--no_header', required=False,
                        action='store_true', help='Disable automatic header completion')

    args = parser.parse_args()

    main(args.i, args.o, not args.no_header)
