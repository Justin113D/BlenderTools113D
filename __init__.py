from . import register as reg

# meta info
bl_info = {
    "name": "Justin113D's Blender Tools",
    "author": "Justin113D",
    "version": (1, 0, 2),
    "blender": (3, 6, 0),
    "location": "",
    "description": "Several tools to make life in blender easier",
    "warning": "",
    "support": 'COMMUNITY',
    "category": "General"}


def register():
    reg.register_classes()


def unregister():
    reg.unregister_classes()


# When refreshing the addon, reload all modules
if locals().get('LOADED'):
    LOADED = False
    from importlib import reload
    from sys import modules

    modules[__name__] = reload(modules[__name__])
    to_reload = {}
    for name, module in modules.items():
        if name.startswith(f"{__package__}."):
            to_reload[name] = module

    for name, module in to_reload.items():
        globals()[name] = reload(module)

    del reload, modules

if __name__ == "__main__":
    register()

LOADED = True
