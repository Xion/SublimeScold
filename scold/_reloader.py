"""
Dependency reloader.

This is needed because ST only tracks changes in the main module of each plugin,
so any additional ones (here, inside ``scold`` package) have to be reloaded
manually if changes are to be registered without restarting the editor.

Based on ideas from:
https://github.com/wbond/sublime_package_control/blob/master/package_control/reloader.py
"""
import imp
import sys


# Modules the plugin is comprised of, sorted topotologically
# according to their import-time dependencies.
MODULES_LOAD_ORDER = [
    'scold.system',
    'scold.util',
    'scold.git',
]


reload_modules = []
for name in sys.modules:
    if name == 'scold' or name.startswith('scold.'):
        if sys.modules[name] is not None:
            reload_modules.append(name)

for name in MODULES_LOAD_ORDER:
    if name in reload_modules:
        imp.reload(sys.modules[name])
