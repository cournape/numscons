from os.path import join, dirname

import numscons

def get_scons_path():
    return join(dirname(numscons.__file__), 'scons-local')
