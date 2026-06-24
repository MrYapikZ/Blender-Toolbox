from . import basic, drive, pattern, pattern_match, playblast_config

modules = [
    basic,
    # drive,
    pattern,
    pattern_match,
    playblast_config
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
