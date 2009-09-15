#! /usr/bin/env python
# Last Change: Wed Jul 30 02:00 PM 2008 J

"""This module defines various utilities used throughout the scons support
library."""

import os
import re

from copy import deepcopy, copy
from subprocess import Popen, PIPE, STDOUT

_START_WITH_MINUS = re.compile('^\s*-')

def popen_wrapper(cmd, merge = False, shell = True, env=None):
    """This works like popen, but it returns both the status and the output.
    expects a list for input.

    If merge is True, then output contains both stdout and stderr.

    Returns: (st, out), where st is an integer (the return status of the
    subprocess, and out the string of the output).

    NOTE:
        - it tries to be robust to find non existing command. For example, is
          cmd starts with a minus, a nonzero status is returned, and no junk is
          displayed on the interpreter stdout."""
    if _START_WITH_MINUS.match(' '.join(cmd)):
        return 1, ''

    if merge:
        stderr = STDOUT
    else:
        stderr = None

    p = Popen(cmd, stdout=PIPE, stderr=stderr, shell=shell, env=env)
    stdout = p.communicate()[0]
    st = p.returncode
    out = ''.join(stdout)
    return st, out

def pkg_to_path(pkg_name):
    """Given a python package name, returns its path from the root.

    Example: numpy.core becomes numpy/core."""
    return os.sep.join(pkg_name.split('.'))

def get_empty(dic, key):
    """Assuming dic is a dictionary with lists as values, returns an empty
    list if key is not found, or a (deep) copy of the existing value if it
    does."""
    try:
        return deepcopy(dic[key])
    except KeyError:
        return []

class NonDefaultKeyError(KeyError):
    """Exception raised when trying to set/get a value from a non default key
    for DefaultDict instances."""
    pass

class DefaultDict(dict):
    """Structure similar to a dictionary, with a restricted set of possible
    keys."""
    @classmethod
    def fromcallable(cls, avkeys, default = None):
        """Class method to instanciate a DefaultDict using a callable for the
        default value.

        Example: DefaultDict.fromcallable(keys, lambda: [])"""
        res = cls(avkeys, default)
        if default is not None:
            for k in res:
                res[k] = default()
        return res

    def __init__(self, avkeys, default = None):
        dict.__init__(self, [(i, default) for i in avkeys])

    def __setitem__(self, key, val):
        if not self.has_key(key):
            raise NonDefaultKeyError(key)
        dict.__setitem__(self, key, val)

    def __copy__(self):
        cls = self.__class__
        cpy = cls.__new__(cls)
        cpy.update(self)
        for k in self.keys():
            cpy[k] = copy(self[k])
        return cpy

def flatten(l):
    """Flatten a list."""
    # XXX: needs testing
    if isinstance(l, list):
        return sum(map(flatten, l), [])
    else:
        return [l]

class partial:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)

# # Copied from scons code...
# import types
# from UserString import UserString
# # Don't "from types import ..." these because we need to get at the
# # types module later to look for UnicodeType.
# InstanceType    = types.InstanceType
# StringType      = types.StringType
# TupleType       = types.TupleType
# if hasattr(types, 'UnicodeType'):
#     UnicodeType = types.UnicodeType
#     def isstring(obj):
#         """Return true if argument is a string."""
#         t = type(obj)
#         return t is StringType \
#             or t is UnicodeType \
#             or (t is InstanceType and isinstance(obj, UserString))
# else:
#     def isstring(obj):
#         """Return true if argument is a string."""
#         t = type(obj)
#         return t is StringType \
#             or (t is InstanceType and isinstance(obj, UserString))
#
def unique(seq):
    """remove duplicate in sequence. Members should be hashable."""
    d = dict([(x, x) for x in seq])
    return d.values()
