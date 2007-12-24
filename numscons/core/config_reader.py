from ConfigParser import SafeConfigParser

config = SafeConfigParser()

_OPTIONS = ['optim', 'warn', 'debug_sym', 'debug', 'thread', 'extra',
            'link_optim']

class Config:
    def __init__(self):
        self._dic = dict([(i, None) for i in _OPTIONS])

    def __getitem__(self, key):
        return self._dic[key]
        
    def __setitem__(self, key, item):
        self._dic[key] = item
        
def get_config(name):
    config.read("compiler.cfg")
    if not config.has_section(name):
        raise ValueError("compiler %s is not configured" % name)

    cfg = Config()

    for o in config.options(name):
        cfg[o] = config.get(name, o)        

    return cfg
