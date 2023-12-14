import logging
import shutil
import subprocess
from abc import abstractmethod
from pathlib import Path
from typing import List

from .compiler import w64devkit_call
from .download import download_lua
from .environment import Config


class Interpreter:
    '''
    A base class for Lua interpreters.
    '''

    @staticmethod
    def mitigation_list() -> List[str]:
        '''
        Returns a list of the available mitigations.
        '''
        return [
            'disable_bytecode',
            'disable_ffi',
            'stdlibrary_sandbox',
            'kikito_sandbox'
        ]

    @staticmethod
    def list() -> List[str]:
        '''
        Returns a list of the available interpreters.
        '''
        return [
            'lua-5.1.5',
            'lua-5.2.4',
            'lua-5.3.6',
            'lua-5.4.6',
            'LuaJIT-4f8736',
            'LuaJIT-rolling',
            'LuaJIT-v2.1.0-beta3',
            'luau'
        ]

    @staticmethod
    def create(name: str, **kwargs) -> 'Interpreter':
        '''
        Creates a new `Interpreter` instance based on the name provided.

        Arguments:
            name: Complete name of the implementation, including version. Has to
                  be one of the values that `Interpreter.list()` returns.
            kwargs: Arguments to pass to the constructor of the implementation.

        Returns:
            The implementation which is an instance of the `Interpreter` class.
        '''
        if name == 'luau':
            return LuauInterpreter(**kwargs)
        if name.startswith('lua-'):
            return LuaInterpreter(name, **kwargs)
        if name.startswith('LuaJIT-'):
            return LuaJITInterpreter(name, **kwargs)
        raise LookupError(f'Interpreter \'{name}\' could not be found.')

    def __init__(self, version: str, mitigations: List[str] | str | None) -> None:
        self.version = version
        self.mitigations: List[str] = []
        self.patched_runner: Path | None = None
        self.exe: Path | None = None
        if isinstance(mitigations, str):
            self.mitigations.append(mitigations)
        elif isinstance(mitigations, list):
            self.mitigations = mitigations
        self.lua_out_dir = Config.TEMP_DIR / str(self)
        self.apply_runtime_mitigations()

    @abstractmethod
    def basename(self) -> str:
        '''
        Returns the base name of the interpreter (without the version).
        '''
        return ''

    def __str__(self) -> str:
        if self.mitigations:
            mitigations_str = '-'.join(self.mitigations)
            return f'{self.version}_{mitigations_str}'
        return self.version

    def apply_runtime_mitigations(self) -> None:
        '''
        Applies all runtime patches relevant for this interpreter.
        '''
        for mitigation in self.mitigations:
            if mitigation == 'kikito_sandbox':
                self.patched_runner = (self.lua_out_dir / 'runner.lua').resolve()

    def apply_compile_patches(self) -> bool:
        '''
        Applies all compile-time patches relevant for this interpreter.

        Returns:
            True whether patching was applied successfully, False if some of the specified
            patches could not be found.
        '''
        base_patch = Config.PATCHES_DIR / f'{self.version}.patch'  # version-specific patch
        if not base_patch.exists():
            base_patch = Config.PATCHES_DIR / f'{self.basename()}.patch'  # version-independent patch

        if base_patch.exists():  # base patch is always applied
            logging.debug(f'Applying patch {base_patch}...')
            logging.debug(f'patch.exe < {base_patch}')
            w64devkit_call('patch.exe', '-p1', '-i', base_patch.resolve(), cwd=self.lua_out_dir)

        for patch in self.mitigations:
            patched = False
            logging.debug(f'Applying patch {patch}...')
            patch_dir = Config.PATCHES_DIR / patch
            patch_file = patch_dir / f'{self.version}.patch'
            if not patch_file.exists():  # search for the version-independent patch
                patch_file = patch_dir / f'{self.basename()}.patch'
            if patch_file.exists():
                logging.debug(f'patch.exe < {patch_file}')
                w64devkit_call('patch.exe', '-p1', '-i', patch_file.resolve(), cwd=self.lua_out_dir)
                patched = True

            dirs_to_copy = [patch_dir / self.basename(), patch_dir / self.version]
            for files_to_copy in dirs_to_copy:
                if files_to_copy.exists():
                    for item in files_to_copy.rglob('*'):
                        if item.is_file():
                            dst = self.lua_out_dir / item.relative_to(files_to_copy)
                            logging.debug(f'copy {item} to {dst}')
                            shutil.copy2(item, dst)
                            patched = True

            if not patched:
                logging.info(f'{str(self)} - Patch {patch} not applicable.')
                return False
        return True

    def run(self, file: Path, cwd: Path | None = None) -> None:
        '''
        Runs a `.lua` file with the compiled interpreter.

        Arguments:
            file: The `.lua` file to be run.
            cwd: Optional working directory of the interpreter.
        '''
        if not self.exe:
            raise RuntimeError('Cannot run because Lua exe was not found. Check if compilation failed.')
        if not file.exists():
            logging.info(f'File \'{file}\' does not exist, compilation of the exploit probably failed. Will not run.')
            return
        try:
            if self.patched_runner:
                with open(file, 'rb') as file_contents:
                    env = Config.ENV
                    env['LUA_PATH'] = str(self.lua_out_dir / '?.lua')
                    subprocess.call([self.exe, self.patched_runner], cwd=cwd, timeout=10.0, stdin=file_contents,
                                    stdout=Config.STDOUT, stderr=Config.STDERR, env=env)
            else:
                subprocess.call([self.exe, file], cwd=cwd, timeout=10.0, stdout=Config.STDOUT, stderr=Config.STDERR)
        except subprocess.TimeoutExpired:
            logging.info(f'{str(self)} - Running {file} timeouted.')

    @abstractmethod
    def unpatched(self) -> 'Interpreter':
        '''
        Returns an `Interpreter` object representing the same version of the
        interpreter without any mitigations applied. Used for exploit compilation.

        Returns:
            An `Interpreter` object without any mitigations applied.
        '''
        pass

    @abstractmethod
    def patched(self, mitigations: List[str] | str) -> 'Interpreter | None':
        '''
        Returns an `Interpreter` object representing the same version of the
        interpreter with provided list of mitigations applied.

        Arguments:
            mitigations: A list of mitigations to be applied.

        Returns:
            An `Interpreter` object with mitigations applied. If the mitigations are incompatible,
            None is returned instead.
        '''
        pass

    @abstractmethod
    def compile(self, clean: bool) -> Path:
        '''
        Compile the implementation.

        Arguments:
            clean: True if compilation should be done on a clean copy of the input folder,
                   False skips the compilation if it was already done before.

        Returns:
            Path to the compiled interpreter `.exe` file.
        '''
        pass


class LuaJITInterpreter(Interpreter):
    def __init__(self, version: str, mitigations: List[str] | str | None = None, clean: bool = False, **kwargs) -> None:
        '''
        An instance of a Lua interpreter. The constructor finds the implementation in
        `interpreters/<version>`, applies all patches specified by the argument and
        found in the `patches` folder and compiles the implementation.

        Arguments:
            version: The version of Lua that should be compiled, has to already exist in the `interpreters` folder.
            mitigations: A list of mitigations to be applied.
            clean: True if compilation should be done on a clean copy of the input folder,
                   False skips the compilation if it was already done before.
        '''
        super().__init__(version, mitigations)
        self.exe = self.compile(clean)

    def basename(self) -> str:
        return 'LuaJIT'

    def patched(self, mitigations: List[str] | str) -> 'LuaJITInterpreter | None':
        interpreter = LuaJITInterpreter(self.version, mitigations)
        if interpreter.exe is None:
            return None
        return interpreter

    def unpatched(self) -> 'LuaJITInterpreter':
        return LuaJITInterpreter(self.version, mitigations=None)

    def compile(self, clean: bool) -> Path | None:
        lua_in_dir = Config.INTERPRETERS_CODE_DIR / self.version
        if not lua_in_dir.exists():
            lua_in_dir = Config.INTERPRETERS_DIR / self.version
        lua_out_dir = self.lua_out_dir
        luajit_exe = lua_out_dir / 'src' / 'luajit.exe'

        if not clean and luajit_exe.exists():
            logging.debug(f'{str(self)} already compiled, skipping.')
            return luajit_exe

        if clean:
            shutil.rmtree(lua_out_dir, ignore_errors=True)
        shutil.copytree(lua_in_dir, lua_out_dir, dirs_exist_ok=True)

        if not self.apply_compile_patches():
            logging.debug(f'Deleting {lua_out_dir}.')
            shutil.rmtree(lua_out_dir)
            return None

        w64devkit_call('make.exe', '-C', lua_out_dir / 'src')
        return luajit_exe


class LuauInterpreter(Interpreter):
    '''
    An instance of a Lua interpreter. The constructor finds the implementation in
    `interpreters/<version>`, applies all mitigations specified by the argument
    and compiles the implementation.

    Arguments:
        mitigations: A list of mitigations from to be applied before compilation.
        clean: True if compilation should be done on a clean copy of the input folder,
               False skips the compilation if it was already done before.
    '''

    def __init__(self, mitigations: List[str] | str | None = None, clean: bool = False, **kwargs) -> None:
        super().__init__('luau', mitigations)
        self.exe = self.compile(clean)

    def basename(self) -> str:
        return 'luau'

    def unpatched(self) -> 'LuauInterpreter':
        return LuauInterpreter(mitigations=None)

    def patched(self, mitigations: List[str] | str) -> 'LuauInterpreter | None':
        interpreter = LuauInterpreter(mitigations)
        if interpreter.exe is None:
            return None
        return interpreter

    def compile(self, clean: bool) -> Path | None:
        lua_in_dir = Config.INTERPRETERS_CODE_DIR / self.version
        if not lua_in_dir.exists():
            lua_in_dir = Config.INTERPRETERS_DIR / self.version
        lua_out_dir = Config.TEMP_DIR / str(self)
        luau_exe = lua_out_dir / 'luau.exe'

        if not clean and luau_exe.exists():
            logging.debug(f'{str(self)} already compiled, skipping.')
            return luau_exe

        if clean:
            shutil.rmtree(lua_out_dir, ignore_errors=True)
        shutil.copytree(lua_in_dir, lua_out_dir, dirs_exist_ok=True)

        if not self.apply_compile_patches():
            logging.debug(f'Deleting {lua_out_dir}.')
            shutil.rmtree(lua_out_dir)
            return None

        w64devkit_call('make.exe', '-C', lua_out_dir, 'config=release', 'luau')
        shutil.copy2(lua_out_dir / 'build/release/luau.exe', luau_exe)
        return luau_exe


class LuaInterpreter(Interpreter):
    '''
    An instance of a PUC-Lua interpreter. The constructor finds the implementation in
    `interpreters/<version>`, applies all mitigations specified by the argument and
    compiles the implementation. If the implementation is not to be found and the `download`
    argument is set to True, it also downloads the source archive from https://www.lua.org
    and extracts it to `interpreters/<version>`.

    Arguments:
        mitigations: A list of mitigations to be applied before compilation.
        clean: True if compilation should be done on a clean copy of the input folder,
                False skips the compilation if it was already done before.
        download: Whether to download the source code if the Lua implementation is not to be found.
    '''

    def __init__(self, version: str, mitigations: List[str] | str | None = None, clean: bool = False, download: bool = False, **kwargs) -> None:
        super().__init__(version, mitigations)
        if download:
            download_lua(version)
        self.exe = self.compile(clean)

    def basename(self) -> str:
        return 'lua'

    def unpatched(self) -> 'LuaInterpreter':
        return LuaInterpreter(self.version, mitigations=None)

    def patched(self, mitigations: List[str] | str) -> 'LuaInterpreter | None':
        interpreter = LuaInterpreter(self.version, mitigations)
        if interpreter.exe is None:
            return None
        return interpreter

    def compile(self, clean: bool) -> Path | None:
        # if someone extracted the Lua implementations to the `interpreters` directory, we're going to use them
        lua_in_dir = Config.INTERPRETERS_CODE_DIR / self.version
        if not lua_in_dir.exists():
            lua_in_dir = Config.INTERPRETERS_DIR / self.version
        lua_out_dir = self.lua_out_dir
        lua_exe = lua_out_dir / 'src' / 'lua.exe'

        if not clean and lua_exe.exists():
            logging.debug(f'{str(self)} already compiled, skipping.')
            return lua_exe

        if clean:
            shutil.rmtree(lua_out_dir, ignore_errors=True)
        shutil.copytree(lua_in_dir / 'src', lua_out_dir / 'src', dirs_exist_ok=True)
        shutil.copy2(lua_in_dir / 'Makefile', lua_out_dir)

        if not self.apply_compile_patches():
            logging.debug(f'Deleting {lua_out_dir}.')
            try:
                shutil.rmtree(lua_out_dir)
            except PermissionError as err:
                logging.debug(f'permission error while removing {str(self)}: {err}')
            return None

        w64devkit_call('make.exe', '-C', lua_out_dir, 'mingw')
        return lua_exe
