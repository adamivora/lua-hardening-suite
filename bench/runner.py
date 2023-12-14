import logging
from typing import Dict, List

from .exploit_checker import ExploitChecker
from .exploits import Exploit
from .interpreters import Interpreter


def run_single(interpreter: Interpreter, exploit: Exploit, exploit_checker: ExploitChecker) -> bool:
    '''
    Run a single interpreter/exploit/exploit checker combination in the Exploit-Mitigation benchmark.

    Arguments:
        interpreter: The Lua implementation to be tested.
        exploit: The exploit to be tested.
        exploit_checker: Exploit checker instance representing the exploit type to test.

    Returns:
        True if the exploit was successful, False otherwise.
    '''
    exploit.prepare()
    exploit.compile(interpreter.unpatched(), exploit_checker)
    exploit_checker.prepare()
    interpreter.run(exploit.exploit_path())
    print(f'{str(interpreter)} - {str(exploit)}: exploited={exploit_checker.is_exploited()}')
    return exploit_checker.is_exploited()


def run_multiple(interpreters: List[Interpreter], exploits: List[Exploit], mitigations: List[str], exploit_checker: ExploitChecker) -> Dict[str, Dict[str, bool]]:
    '''
    Run a combination of intepreters, exploits, mitigations and an exploit checker in the Exploit-Mitigation benchmark.

    Arguments:
        interpreters: List of Lua implementation to be tested.
        exploits: List of exploits to be tested.
        mitigations: List of mitigations to be (independently) applied to the Lua implementations.
        exploit_checker: Exploit checker instance representing the exploit type to test.

    Returns:
        A dictionary where the keys represent the different Lua implementations (a mitigation creates a new Lua implementation), and the values are dictionaries,
        where the keys are exploit names and values are booleans representing whether the exploit on that implementation was successful.

        An example of such an output:
        ```
        {
            'lua-1.2.3': {
                'exploit-1': True if exploited, False otherwise,
                'exploit-2': ...,
            },
            'lua-1.2.3_patch-1': {
                ...
            },
            ...,
            'lua-4.5.6': {
                ...
            },
            ...
        }
        ```
    '''
    exploited: Dict[str, Dict[str, bool]] = {}
    for interpreter in interpreters:
        exploited[str(interpreter)] = {}
        for exploit in exploits:
            exploited[str(interpreter)][str(exploit)] = run_single(interpreter, exploit, exploit_checker)
        for mitigation in mitigations:
            patched = interpreter.patched(mitigation)
            if not patched:
                logging.info(f'Mitigation \'{mitigation}\' not applicable to \'{str(interpreter)}\'.')
                continue
            exploited[str(patched)] = {}
            for exploit in exploits:
                exploited[str(patched)][str(exploit)] = run_single(patched, exploit, exploit_checker)

    return exploited
