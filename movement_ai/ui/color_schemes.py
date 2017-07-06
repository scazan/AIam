from collections import OrderedDict

color_schemes = OrderedDict()

color_schemes["white"] = {
    "background": (1.0, 1.0, 1.0, 0.0),
    "unit_cube": (0, 0, 0, 0.2),
    "floor": (0.2, 0.2, 0.2, 1),
    "focus": (0, 0, 0, 0.2),
    "input": (0, 1, 0),
    "output": (0, 0, 0),
    "io_blend": (0, 0, 1),
    "shadow": (.9, .9, .9),
    }

color_schemes["black"] = {
    "background": (0.0, 0.0, 0.0, 0.0),
    "unit_cube": (1, 1, 1, 0.2),
    "floor": (0.3, 0.3, 0.3, 1),
    "focus": (1, 1, 1, 0.2),
    "input": (0, 1, 0),
    "output": (1, 1, 1),
    "io_blend": (0, 0, 1),
    "shadow": (0, 0, 0),
    }
