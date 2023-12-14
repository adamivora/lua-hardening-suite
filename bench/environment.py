import logging
import os
import subprocess
from pathlib import Path
from typing import Dict


class Config:
    CODE_DIR = Path(__file__).parent.parent.resolve()
    '''
    Path to the benchmark root.
    '''

    INTERPRETERS_CODE_DIR = CODE_DIR / 'interpreters'
    '''
    The base directory for all interpreters that are added as submodules to this repository (LuaJIT, Luau).
    '''

    PATCHES_DIR = CODE_DIR / 'patches'
    '''
    The source directory for the patches to be applied to the implementations.
    '''

    EXPLOITS_DIR = CODE_DIR / 'exploits'
    '''
    The source directory for the exploits.
    '''

    WORKING_DIR = Path('.').resolve()
    '''
    The working directory of the codebase. Defaults to the process working directory, but can be overriden.
    '''

    INTERPRETERS_DIR = WORKING_DIR / 'interpreters'
    '''
    The base directory for all interpreters that are downloaded dynamically and a part of the working directory (PUC-Lua).
    '''

    TEMP_DIR = WORKING_DIR / 'temp'
    '''
    The subdirectory of the working directory where all temporary files are stored (compiled exploits and interpreters).
    '''

    TOOLS_DIR = WORKING_DIR / 'tools'
    '''
    Contains tools needed to compile exploits (`w64devkit`).
    '''

    ARBITRARY_WRITE_DIR = WORKING_DIR / 'exploited'
    '''
    The directory where the exploits should write in the case of the `ArbitraryWriteChecker` exploit checker.
    '''

    ENV: Dict[str, str] = {}
    '''
    Contains the environment variables that all calls to `w64devkit` are going to use.
    '''

    LOGGING_LEVEL: str = 'none'

    STDOUT: int | None = None
    '''
    The default input to the `stdout` argument for `subprocess.call` calls.
    Used to hide standard output on the `none` logging level.
    '''

    STDERR: int | None = None
    '''
    The default input to the `stderr` argument for `subprocess.call` calls.
    Used to hide standard error output on the `none` logging level.
    '''
    @staticmethod
    def set_working_dir(work_dir: Path):
        '''
        Sets the working directory where all the files created by this project will be written to.
        '''
        Config.WORKING_DIR = work_dir.resolve()
        Config.INTERPRETERS_DIR = Config.WORKING_DIR / 'interpreters'
        Config.TEMP_DIR = Config.WORKING_DIR / 'temp'
        Config.TOOLS_DIR = Config.WORKING_DIR / 'tools'
        Config.ARBITRARY_WRITE_DIR = Config.WORKING_DIR / 'exploited'
        Config.ENV = Config.refreshenv()

    @staticmethod
    def set_logging_level(level: str):
        '''
        Set the logging level.

        Arguments:
            level: Logging level to set. Must be one of `debug`, `info`, or `none`.
        '''
        Config.LOGGING_LEVEL = level
        logger = logging.getLogger()
        if level == 'debug':
            Config.STDOUT = None
            Config.STDERR = None
            logger.setLevel(logging.DEBUG)
        elif level == 'info':
            Config.STDOUT = subprocess.DEVNULL
            Config.STDERR = None
            logger.setLevel(logging.INFO)
        elif level == 'none':
            Config.STDOUT = subprocess.DEVNULL
            Config.STDERR = subprocess.DEVNULL
            logger.setLevel(logging.CRITICAL)  # we use only debug and info levels in the codebase
        else:
            raise RuntimeError(f'Logging level \'{level}\' not found.')

    @staticmethod
    def refreshenv() -> Dict[str, str]:
        '''
        Gets a copy of the environment variables and tweaks them to make compilation work.

        Returns:
            The environment dictionary.
        '''
        env = os.environ.copy()
        env['PATH'] = str((Config.TOOLS_DIR / 'w64devkit' / 'bin').resolve())
        env['MAKEFLAGS'] = '-j8'
        env['CC'] = 'gcc'
        env['CXX'] = 'g++'
        return env
