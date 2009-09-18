# INPUTS:
#   ICC_ABI: x86, amd64

_ARG2ABI = {'x86': 'ia32', 'amd64': 'em64t', 'default': 'ia32'}

def get_abi(env):
    try:
        abi = env['ICC_ABI']
    except KeyError:
        abi = 'default'

    try:
        return _ARG2ABI[abi]
    except KeyError:
        ValueError("Unknown abi %s" % abi)
