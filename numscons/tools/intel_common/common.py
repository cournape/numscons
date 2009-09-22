# INPUTS:
#   ICC_ABI: x86, amd64

_ARG2ABI = {'x86': 'ia32', 'amd64': 'amd64', 'default': 'ia32'}

def get_abi(env, lang='C'):
    if lang == 'C' or lang == 'CXX':
        try:
            abi = env['ICC_ABI']
        except KeyError:
            abi = 'default'
    elif lang == 'FORTRAN':
        try:
            abi = env['IFORT_ABI']
        except KeyError:
            abi = 'default'

    try:
        return _ARG2ABI[abi]
    except KeyError:
        ValueError("Unknown abi %s" % abi)
