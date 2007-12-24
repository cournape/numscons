from ConfigParser import SafeConfigParser, ConfigParser

from numscons.core.utils import partial

_OPTIONS = ['optim', 'warn', 'debug_sym', 'debug', 'thread', 'extra',
            'link_optim']

class Config:
    """Place holder for compiler configuration."""
    def __init__(self):
        self._dic = dict([(i, None) for i in _OPTIONS])

    def __getitem__(self, key):
        return self._dic[key]
        
    def __setitem__(self, key, item):
        self._dic[key] = item
        
class CompilerConfig:
    """Put config objects value into a dictionary usable by scons. C compiler
    version"""
    def __init__(self, cfg):
        self._cfg = cfg

    def get_flags_dict(self):
        d = {'NUMPY_OPTIM_CFLAGS' : self._cfg['optim'],
             'NUMPY_OPTIM_LDFLAGS' : self._cfg['link_optim'],
             'NUMPY_WARN_CFLAGS' : self._cfg['warn'],
             'NUMPY_THREAD_CFLAGS' : self._cfg['thread'],
             'NUMPY_EXTRA_CFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_CFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_SYMBOL_CFLAGS' : self._cfg['debug_sym']}
        for k, v in d.items():
            if v is None:
                d[k] = []
            else:
                d[k] = v.split()
        return d
        
class F77CompilerConfig:
    """Put config objects value into a dictionary usable by scons. Fortran 77
    compiler version"""
    def __init__(self, cfg):
        self._cfg = cfg

    def get_flags_dict(self):
        d = {'NUMPY_OPTIM_FFLAGS' : self._cfg['optim'],
             'NUMPY_WARN_FFLAGS' : self._cfg['warn'],
             'NUMPY_THREAD_FFLAGS' : self._cfg['thread'],
             'NUMPY_EXTRA_FFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_FFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_SYMBOL_FFLAGS' : self._cfg['debug_sym']}
        for k, v in d.items():
            if v is None:
                d[k] = []
            else:
                d[k] = v.split()
        return d
        
def get_config(name, cfgfname):
    config = ConfigParser()
    config.read(cfgfname)
    if not config.has_section(name):
        raise ValueError("compiler %s is not configured" % name)

    cfg = Config()

    for o in config.options(name):
        cfg[o] = config.get(name, o)        

    return cfg

get_cc_config = partial(get_config, cfgfname = "compiler.cfg")
get_fc_config = partial(get_config, cfgfname = "fcompiler.cfg")

if __name__ == '__main__':
    cfg = get_cc_config('gcc')
    cc = CompilerConfig(cfg)
    print cc.get_flags_dict()

    cfg = get_fc_config('gnu')
    cc = CompilerConfig(cfg)
    print cc.get_flags_dict()
