# Lua Hardening Suite
This repo serves as a collection of possible ways how to execute potentially malicious code on Windows with various Lua implementations and possible ways how
to mitigate them at the source-code-level, or Lua-level. If you are trying to sandbox your Lua implementation, then this repository may serve you as
a primer to see what types of behaviour to protect against. The list of exploits and mitigations is certainly not complete.

Contributions of new exploit types, mitigations, or Lua implementations are definitely welcome.

## Exploit Types
The type of exploit considered in this benchmark so far is writing a file to a path predefined in the settings. All the "exploits" included here are
harmless in the sense their only behaviour is to try to write to that file using various methods. However, arming these exploits with malicious payloads
is quite easy, as most of them try to spawn an instance of `cmd.exe` to write to the file.

## Requirements
This benchmark only runs on Windows. You need to have [Git](https://git-scm.com/) and a recent version of [Python](https://www.python.org/) installed
before running the software. Internet access is required to download the other dependencies for this benchmark (the Python code does this automatically):
- [w64devkit](https://github.com/skeeto/w64devkit) to compile the Lua implementations and exploits
- source code tarballs of different [PUC-Lua](https://www.lua.org/ftp/) versions

## Setup
1. After getting a copy of this repository, clone the submodules of this repository (which are the LuaJIT and Luau implementations).
```bash
git submodule update --init --recursive
```
2. Install Python dependencies from the `requirements.txt` using any Python workflow you are already using, recommend using a virtual environment.
```bash
pip install -r requirements.txt
```
3. Run the benchmark. From the root directory of this benchmark, run the `bench` module.
```bash
python -m bench --help
```

## Examples
Shows the help and all possible command-line options with their descriptions.
```bash
python -m bench --help
```

Tests a single Lua implementation, single exploit and single mitigation.
```bash
python -m bench --interpreter lua-5.4.6 --exploit std_os_execute --mitigation stdlibrary_sandbox
```

Tests all Lua implementations, all exploits and all mitigations implemented. This takes around 10 minutes to complete.
```bash
python -m bench --all-interpreters --all-exploits --all-mitigations
```

## Available Lua Implementations
These are the supported Lua implementations of this benchmark:
- [PUC-Lua](https://www.lua.org/home.html)
  - 5.1.5 (`lua-5.1.5`)
  - 5.2.4 (`lua-5.2.4`)
  - 5.3.6 (`lua-5.3.6`)
  - 5.4.6 (`lua-5.4.6`)
- [LuaJIT](https://luajit.org/luajit.html)
  - [4f8736](https://github.com/LuaJIT/LuaJIT/commit/4f87367b0335d442d3e9dac3fd8ac2788a5756bc) (`luajit-4f8736`)
  - [v2.1.0-beta3](https://github.com/LuaJIT/LuaJIT/commit/8271c643c21d1b2f344e339f559f2de6f3663191) (`luajit-v2.1.0-beta3`)
  - [v2.1-ROLLING](https://github.com/LuaJIT/LuaJIT/commit/43d0a19158ceabaa51b0462c1ebc97612b420a2e) (`luajit-rolling`)
- [Luau](https://luau-lang.org/)
  - 0.606 (`luau`)

## Available Exploit POCs
- Bytecode Exploits
  - [LuaJIT-4f8736 bytecode exploit](https://www.corsix.org/content/malicious-luajit-bytecode) by corsix (`bytecode_corsix`)
- FFI Exploits
  - Spawning a process using the [CreateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa) function from Win32 API (`ffi_createprocess`)
  - Loading a DLL using the `ffi.load` function (`ffi_load`)
  - Running Windows shellcode from an area of memory made executable by the [VirtualAlloc](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc) Win32 API (`ffi_virtualalloc`)
- Standard Library Exploits
  - Using Lua `io.write` function to write to an arbitrary file (`std_io_write`)
  - Using Lua `os.execute` function to run arbitrary process (`std_os_execute`)

## Available Mitigations
Keep in mind these mitigations are proofs of concepts and there is no guarantee they will make your Lua implementation secure.
- Source code patches
  - disabling bytecode (`disable_bytecode`)
  - disabling FFI for LuaJIT interpreters (`disable_ffi`)
  - replacing some C Standard Library functions with "safe" variants (`stdlibrary_sandbox`)
    - just a simple POC, only `fwrite` and `system` are replaced
- Lua-level mitigations
  - kikito's [sandbox.lua](https://github.com/kikito/lua-sandbox) (`kikito_sandbox`)

## Acknowledgements
This project has been financially supported by a [Red Hat](https://www.redhat.com/) scholarship for open-source projects. Thank you for the support!