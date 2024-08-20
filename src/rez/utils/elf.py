# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the Rez Project


"""
Functions that wrap readelf/patchelf utils on linux.
"""
import os
from shlex import quote
import subprocess

from rez.utils.filesystem import make_path_writable
from rez.utils.execution import Popen


def get_rpaths(elfpath):
    """Get rpaths/runpaths from header.
    """

    # stdout lines look like:
    # 0x000000000000000f (RPATH) Library rpath: [/xxx:/yyy]
    #
    out = _run("readelf", "-d", elfpath)

    # parse out rpath/runpath
    for line in out.split('\n'):
        parts = line.strip().split()
        if "(RPATH)" in parts or "(RUNPATH)" in parts:
            txt = parts[-1]
            txt = txt[1:-1]  # strip [ and ]
            rpaths = txt.split(':')

            return rpaths or []

    return []


def patch_rpaths(elfpath, rpaths):
    """Replace an elf's rpath header with those provided.
    """

    # this is a hack to get around #1074
    # I actually hit a case where patchelf was installed as a rez suite tool,
    # causing '$ORIGIN' to be expanded early (to empty string).
    # TODO remove this hack when bug is fixed
    #
    env = os.environ.copy()
    env["ORIGIN"] = "$ORIGIN"

    with make_path_writable(elfpath):
        if rpaths:
            _run("patchelf", "--set-rpath", ':'.join(rpaths), elfpath, env=env)
        else:
            _run("patchelf", "--remove-rpath")


def _run(*nargs, **popen_kwargs):
    proc = Popen(
        nargs,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **popen_kwargs
    )

    out, err = proc.communicate()

    if proc.returncode:
        cmd_ = ' '.join(quote(x) for x in nargs)

        raise RuntimeError(
            "Command %s - failed with exitcode %d: %s"
            % (cmd_, proc.returncode, err.strip().replace('\n', "\\n"))
        )

    return out
