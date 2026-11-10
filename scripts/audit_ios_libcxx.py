#!/usr/bin/env python3
"""Fails when a static library imports libc++ symbols the OS lacks on iOS MIN.

dyld binds these at launch, so one of them kills the app before main() on
older iOS ("Symbol not found ... Expected in: /usr/lib/libc++.1.dylib").
Versions: libc++ __configuration/availability.h (Xcode 16.4, LLVM 19).
Also fails when an object declares a deployment target above MIN.

usage: audit_ios_libcxx.py MIN LIB.a [LIB.a ...]
"""
import re
import subprocess
import sys

FEATURES = [
    ('FILESYSTEM_LIBRARY', (13, 0), r'St3__14__fs10filesystem'),
    ('SYNC', (14, 0), r'__libcpp_atomic_(wait|monitor)|__cxx_atomic_notify_(one|all)'),
    ('TO_CHARS_FLOATING_POINT', (16, 5), r'St3__18to_charsEPcS0_[def]'),
    ('VERBOSE_ABORT', (16, 5), r'St3__122__libcpp_verbose_abort'),
    ('PMR', (17, 0), r'St3__13pmr'),
    ('INIT_PRIMARY_EXCEPTION', (18, 0), r'__cxa_init_primary_exception'),
    ('PRINT', (18, 0), r'__is_posix_terminal'),
    ('TZDB', (18, 4), r'St3__16chrono.*(tzdb|time_zone)'),
    ('BAD_FUNCTION_CALL_KEY_FUNCTION', (18, 4), r'St3__117bad_function_call4what'),
    ('BAD_EXPECTED_ACCESS_KEY_FUNCTION', (18, 4), r'St3__119bad_expected_accessIvE'),
]


def version(s):
    return tuple(int(x) for x in (s.split('.') + ['0'])[:2])


def main():
    minimum = version(sys.argv[1])
    bad = 0
    for lib in sys.argv[2:]:
        nm = subprocess.run(['nm', '-A', '-u', lib], capture_output=True, text=True, check=True)
        for line in nm.stdout.splitlines():
            obj, _, sym = line.rpartition(': ')
            sym = sym.split()[-1] if sym.split() else ''
            for name, ios, rx in FEATURES:
                if ios > minimum and re.search(rx, sym):
                    print(f'{obj}: {sym} ({name}, iOS {ios[0]}.{ios[1]})')
                    bad += 1
        otool = subprocess.run(['otool', '-l', lib], capture_output=True, text=True, check=True)
        targets = {version(m) for m in re.findall(r'^\s*minos (\S+)', otool.stdout, re.M)}
        print(f'{lib}: object deployment targets {sorted(targets)}')
        above = [t for t in targets if t > minimum]
        if above:
            print(f'{lib}: objects built for {sorted(above)}, above {sys.argv[1]}')
            bad += 1
    print('OK' if not bad else f'{bad} problem(s) for iOS {sys.argv[1]}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
