import argparse
from os import getcwd
from pathlib import Path
from pprint import pprint
from sys import exit
from typing import List

from .download import disable_downloads
from .environment import Config
from .exploit_checker import ExploitChecker
from .exploits import Exploit
from .interpreters import Interpreter
from .runner import run_multiple, run_single


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='python -m bench',
        description='Lua Hardening Suite',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--log-level', type=str, default='none',
                        choices=['debug', 'info', 'none'], help='The logging verbosity of the benchmark.')
    parser.add_argument('--workdir', type=str, default=getcwd(),
                        help='The working directory for the benchmark. All needed files will be created in this directory.')
    parser.add_argument('--no-download', action='store_true',
                        help='Do not allow downloads of w64devkit and PUC-Lua.'
                             'That means you have to get the copies of them yourself and extract them to the correct folders.')
    parser.add_argument('--interpreter', type=str, default='LuaJIT-4f8736', choices=Interpreter.list(),
                        help='The implementation of Lua to be tested.')
    parser.add_argument('--exploit-checker', type=str, default='arbitrary-write', choices=ExploitChecker.list(),
                        help='The exploit checker to be used.')
    parser.add_argument('--exploit', type=str, default='bytecode_corsix', choices=Exploit.list(),
                        help='The exploit to be tested.')
    parser.add_argument('--mitigation', type=str, default=None, required=False, choices=Interpreter.mitigation_list(),
                        help='The mitigation to be tested.')
    parser.add_argument('--all-interpreters', action='store_true', help='Test ALL available Lua interpreters.')
    parser.add_argument('--all-exploits', action='store_true', help='Test ALL available exploits.')
    parser.add_argument('--all-mitigations', action='store_true', help='Test ALL available mitigations.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.no_download:
        disable_downloads()
    Config.set_working_dir(Path(args.workdir))
    Config.set_logging_level(args.log_level)
    download = not args.no_download

    exploit_checker: ExploitChecker = ExploitChecker.create(args.exploit_checker)

    print('Preparing environment (can take a long time)... You can see the compilation progress by re-running with `--log-level info`.')
    single = not args.all_interpreters and not args.all_exploits and not args.all_mitigations
    if single:
        interpreter = Interpreter.create(args.interpreter, download=download)
        exploit = Exploit.create(args.exploit)
        if args.mitigation:
            interpreter = interpreter.patched(args.mitigation)
            if interpreter is None:
                raise RuntimeError(f'Mitigation \'{args.mitigation}\' not available for \'{str(interpreter)}\'.')
        exploited = run_single(interpreter, exploit, exploit_checker)
        exit(int(exploited))  # return the exploit status in the program return code
    else:
        interpreters: List[Interpreter] = []
        if args.all_interpreters:
            interpreters = [Interpreter.create(version, download=download) for version in Interpreter.list()]
        else:
            interpreters.append(Interpreter.create(args.interpreter, download=download))

        exploits: List[Exploit] = []
        if args.all_exploits:
            exploits = [Exploit.create(exploit) for exploit in Exploit.list()]
        else:
            exploits.append(Exploit.create(args.exploit))

        mitigations: List[str] = []
        if args.all_mitigations:
            mitigations = [mitigation for mitigation in Interpreter.mitigation_list()]
        elif args.mitigation:
            mitigations.append(args.mitigation)

        print('Interpreters to test:')
        pprint([str(interpreter) for interpreter in interpreters])

        print('Exploits to test:')
        pprint([str(exploit) for exploit in exploits])

        print('Mitigations to test:')
        pprint(mitigations)
        exploited = run_multiple(interpreters, exploits, mitigations, exploit_checker)
        pprint(exploited)
