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
from enum import Enum, auto


class OutType(Enum):
    html = 'html'
    pdf = 'pdf'


HEADER = {'title': 'Generic title',
          'authors': 'Generic author',
          'doctype': 'lnotes',
          'typing': 'plain'}

_BINARY_URLS = {'Linux': 'https://github.com/somik861/mu_cmake/releases/download/v0.0.2-pre/linux64_gcc8.tar.gz',
                'Windows': 'https://github.com/somik861/mu_cmake/releases/download/v0.0.2-pre/win64_cygwin.zip'}
BINARY_URL = _BINARY_URLS[platform.system()]

FILES_FOLDER_NAME = os.path.join('mu_gen_files', platform.system())
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
HTML_PATH = Path(os.path.join(FILES_FOLDER_PATH, 'html'))
TEX_PATH = Path(os.path.join(FILES_FOLDER_PATH, 'tex'))
FONTS_PATH = Path(os.path.join(FILES_FOLDER_PATH, 'fonts'))


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

    assert _validate_files(), 'Files werent correctly downloaded, ' + \
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


def get_html(source: str) -> bytes:
    result = subprocess.run([MU_BINARY_PATH, '--html', '--embed', HTML_PATH],
                            input=source.encode(encoding='utf-8'), capture_output=True)

    tex_cache = Path(os.path.join(FILES_FOLDER_PATH, 'texmf_cache'))
    tex_cache.mkdir(parents=True, exist_ok=True)

    os.putenv('TEXINPUTS', str(TEX_PATH))
    os.putenv('OSFONTDIR', str(FONTS_PATH))
    os.putenv('TEXMFCACHE', str(tex_cache))

    result = subprocess.run([SVGTEX_BINARY_PATH],
                            input=result.stdout, capture_output=True)

    rmtree(tex_cache, ignore_errors=True)
    return result.stdout


def get_pdf(source: str) -> bytes:

    build_path = Path(os.path.join(FILES_FOLDER_PATH, 'build_f'))
    build_path.mkdir(parents=True, exist_ok=True)
    tex_cache = Path(os.path.join(FILES_FOLDER_PATH, 'texmf_cache'))
    tex_cache.mkdir(parents=True, exist_ok=True)

    os.putenv('TEXINPUTS', str(TEX_PATH))
    os.putenv('OSFONTDIR', str(FONTS_PATH))
    os.putenv('TEXMFCACHE', str(tex_cache))

    subprocess.run(['mtxrun', '--generate'], capture_output=True)
    subprocess.run(['context', '--make'], capture_output=True)

    txt_file = os.path.join(build_path, 'source.txt')
    open(txt_file, 'w', encoding='utf-8').write(source)

    result = subprocess.run([MU_BINARY_PATH, txt_file], capture_output=True)


    tex_file = os.path.join(build_path, 'source.tex')
    open(tex_file, 'w', encoding='utf-8').write(result.stdout.decode(encoding='utf-8'))

    subprocess.run(['context', tex_file], cwd=build_path, capture_output=True)
    data = open(os.path.join(build_path, 'source.pdf'), 'rb').read()

    rmtree(build_path, ignore_errors=True)
    rmtree(tex_cache, ignore_errors=True)
    return data


def main(type_: OutType, inp: str, out: str, complete_header: bool = True) -> None:
    extension = '.' + type_.value
    if not out.endswith(extension):
        out += extension

    init_if_needed()

    source = open(inp, 'r', encoding='utf-8').read()

    if complete_header:
        source = _complete_header(source)

    if type_ is OutType.html:
        html = get_html(source)
        open(out, 'w', encoding='utf-8').write(html.decode(encoding='utf-8'))

    if type_ is OutType.pdf:
        pdf = get_pdf(source)
        open(out, 'wb').write(pdf)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('type', metavar='TYPE', type=str,
                        choices=['html', 'pdf'])
    parser.add_argument('i', metavar='IN_FILE', type=str, help='Input file')
    parser.add_argument('o', metavar='OUT_FILE', type=str, help='Output file')
    parser.add_argument('--no_header', required=False,
                        action='store_true', help='Disable automatic header completion')

    args = parser.parse_args()

    main(OutType(args.type), args.i, args.o, not args.no_header)
