
import sys
from import_hook import import_hook_manager

backends = {'tk': 'TkAgg',
            'gtk': 'GTKAgg',
            'wx': 'WXAgg',
            'qt': 'Qt4Agg', # qt3 not supported
            'qt4': 'Qt4Agg',
            'osx': 'MacOSX'}

# We also need a reverse backends2guis mapping that will properly choose which
# GUI support to activate based on the desired matplotlib backend.  For the
# most part it's just a reverse of the above dict, but we also need to add a
# few others that map to the same GUI manually:
backend2gui = dict(zip(backends.values(), backends.keys()))
backend2gui['Qt4Agg'] = 'qt'
# In the reverse mapping, there are a few extra valid matplotlib backends that
# map to the same GUI support
backend2gui['GTK'] = backend2gui['GTKCairo'] = 'gtk'
backend2gui['WX'] = 'wx'
backend2gui['CocoaAgg'] = 'osx'


def find_gui_and_backend():
    """Return the gui and mpl backend."""
    matplotlib = sys.modules['matplotlib']
    # WARNING: this assumes matplotlib 1.1 or newer!!
    backend = matplotlib.rcParams['backend']
    # In this case, we need to find what the appropriate gui selection call
    # should be for IPython, so we can activate inputhook accordingly
    gui = backend2gui.get(backend, None)
    return gui, backend


def patched_interactive(is_interactive):
    """ Patch matplotlib function 'interactive' """
    matplotlib = sys.modules['matplotlib']
    gui, backend = find_gui_and_backend()
    # if is_interactive_backend(backend) == is_interactive:
    #     # set interactive mode only for interactive backends
    #     # and non-interactive mode for non-interactive backends
    #     matplotlib.real_interactive(is_interactive)
    # TODO: turn off gui?
    matplotlib.real_interactive(is_interactive)


def patched_use(interpreter):
    """ Patch matplotlib function 'use' """
    def patched_use_inner(*args, **kwargs):
        matplotlib = sys.modules['matplotlib']
        matplotlib.real_use(*args, **kwargs)
        gui, backend = find_gui_and_backend()
        interpreter.enableGui(gui)
    return patched_use_inner


def is_interactive_backend(backend):
    """ Check if backend is interactive """
    matplotlib = sys.modules['matplotlib']
    from matplotlib.rcsetup import interactive_bk, non_interactive_bk
    if backend in interactive_bk:
        return True
    elif backend in non_interactive_bk:
        return False
    else:
        return matplotlib.is_interactive()


def activate_matplotlib(interpreter):
    """Set interactive to True for interactive backends."""
    def activate_matplotlib_inner():
        matplotlib = sys.modules['matplotlib']
        gui, backend = find_gui_and_backend()
        interpreter.enableGui(gui)
        is_interactive = is_interactive_backend(backend)
        if is_interactive:
            if not matplotlib.is_interactive():
                sys.stdout.write("Backend %s is interactive backend. Turning interactive mode on.\n" % backend)
            matplotlib.interactive(True)
        else:
            if matplotlib.is_interactive():
                sys.stdout.write("Backend %s is non-interactive backend. Turning interactive mode off.\n" % backend)
            matplotlib.interactive(False)
    return activate_matplotlib_inner


def init_matplotlib(interpreter):
    import_hook_manager.add_module_name("matplotlib", activate_matplotlib(interpreter))
    import_hook_manager.add_function("matplotlib", "use", patched_use(interpreter))
    import_hook_manager.add_function("matplotlib", "interactive", patched_interactive)