import logging
import tarfile
import zipfile

import requests

from .environment import Config

DOWNLOAD_ALLOWED = True


def disable_downloads():
    '''
    Disables any download-related functionalities of this repository.
    '''

    global DOWNLOAD_ALLOWED
    DOWNLOAD_ALLOWED = False


def download_w64devkit() -> None:
    '''
    Downloads `w64devkit` binary release which contains tools needed to compile the interpreters
    and the exploits.
    '''
    w64devkit_dir = Config.TOOLS_DIR / 'w64devkit'
    if w64devkit_dir.exists():
        logging.debug(f'w64devkit already downloaded, skipping.')
        return

    if not DOWNLOAD_ALLOWED:
        raise RuntimeError('Downloading not allowed!')

    url = 'https://github.com/skeeto/w64devkit/releases/download/v1.21.0/w64devkit-1.21.0.zip'
    logging.info(f'Downloading w64devkit from {url}.')

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        archive_path = Config.TEMP_DIR / 'w64devkit-1.21.0.zip'
        archive_path.parent.mkdir(exist_ok=True, parents=True)
        with open(archive_path, 'wb') as f:
            f.write(response.raw.read())

        file = zipfile.ZipFile(archive_path)
        file.extractall(Config.TOOLS_DIR)
        file.close()
        archive_path.unlink()


def download_lua(version: str) -> None:
    '''
    Downloads a PUC-Lua source code from https://www.lua.org and extracts it to the working
    directory.

    Args:
        version: The version of lua to download, starting with the `lua-` prefix.
    '''
    lua_dir = Config.INTERPRETERS_DIR / version
    if lua_dir.exists() or (Config.INTERPRETERS_CODE_DIR / version).exists():
        logging.debug(f'{version} already downloaded, skipping.')
        return

    if not DOWNLOAD_ALLOWED:
        raise RuntimeError('Downloading not allowed!')

    url = f'https://www.lua.org/ftp/{version}.tar.gz'
    logging.info(f'Downloading {version} from {url}.')

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        archive_path = Config.TEMP_DIR / f'{version}.tar.gz'
        archive_path.parent.mkdir(exist_ok=True, parents=True)
        with open(archive_path, 'wb') as f:
            f.write(response.raw.read())

        file = tarfile.open(archive_path)
        file.extractall(Config.INTERPRETERS_DIR)
        file.close()
        archive_path.unlink()
