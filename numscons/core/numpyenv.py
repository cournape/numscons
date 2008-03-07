# This module cannot be imported directly, because it needs scons module.

from SCons.Environment import Environment

class NumpyEnvironment(Environment):
    def __init__(self, *args, **kw):
        Environment.__init__(self, *args, **kw)

