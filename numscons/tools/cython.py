"""Small tool to create a Cython builder."""
import SCons
from SCons.Builder import Builder
from SCons.Action import Action

cythonAction = Action("$CYTHONCOM", "$CYTHONCOMSTR")

def create_builder(env):
    try:
        cython = env['BUILDERS']['Cython']
    except KeyError:
        cython = SCons.Builder.Builder(
                  action = "$CYTHONCOM",
                  emitter = {},
                  suffix = cython_suffix_emitter,
                  single_source = 1)
        env['BUILDERS']['Cython'] = cython

    return cython

def cython_suffix_emitter(env, source):
    return "$CYTHONCFILESUFFIX"

def generate(env):
    env["CYTHON"] = "cython"
    env["CYTHONCOM"] = "$CYTHON $CYTHONFLAGS -o $TARGET $SOURCE"
    env["CYTHONCFILESUFFIX"] = ".c"

    c_file, cxx_file = SCons.Tool.createCFileBuilders(env)

    c_file.suffix['.pyx'] = cython_suffix_emitter
    c_file.add_action('.pyx', cythonAction)

    create_builder(env)

def exists(env):
    return env.Detect(["cython"])
