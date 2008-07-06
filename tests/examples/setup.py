import os
import os.path

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('examples',parent_package,top_path)

    from numscons import get_version
    import numscons
    print "++++++++++++++++++++++++++++++++"
    print "Numscons Version is %s" % get_version()
    print "++++++++++++++++++++++++++++++++"
    config.add_subpackage('checkers')
    config.add_subpackage('checklib')
    config.add_subpackage('ctypesext')
    config.add_subpackage('fortran')
    config.add_subpackage('hook')
    #config.add_subpackage('gnu2ms')
    config.add_subpackage('pyext')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)
