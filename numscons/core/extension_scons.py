#! /usr/bin/env python
# Last Change: Sun Jan 06 09:00 PM 2008 J

def createStaticExtLibraryBuilder(env):
    """This is a utility function that creates the StaticExtLibrary Builder in
    an Environment if it is not there already.

    If it is already there, we return the existing one."""
    import SCons.Action

    try:
        static_extlib = env['BUILDERS']['StaticExtLibrary']
    except KeyError:
        action_list = [ SCons.Action.Action("$ARCOM", "$ARCOMSTR") ]
        if env.Detect('ranlib'):
            ranlib_action = SCons.Action.Action("$RANLIBCOM", "$RANLIBCOMSTR")
            action_list.append(ranlib_action)

    static_extlib = SCons.Builder.Builder(action = action_list,
                                          emitter = '$LIBEMITTER',
                                          prefix = '$LIBPREFIX',
                                          suffix = '$LIBSUFFIX',
                                          src_suffix = '$OBJSUFFIX',
                                          src_builder = 'SharedObject')

    env['BUILDERS']['StaticExtLibrary'] = static_extlib
    return static_extlib
