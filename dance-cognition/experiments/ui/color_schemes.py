from collections import OrderedDict

color_schemes = OrderedDict()

color_schemes["white"] = {
    "background": (1.0, 1.0, 1.0, 0.0),
    "unit_cube": (0, 0, 0, 0.2),
    "floor": (0, 0, 0, 0.2),
    "focus": (0, 0, 0, 0.2),
    "input": (0, 1, 0),
    "output": (0, 0, 0),
    }

color_schemes["black"] = {
    "background": (0.0, 0.0, 0.0, 0.0),
    "unit_cube": (1, 1, 1, 0.2),
    "floor": (1, 1, 1, 0.2),
    "focus": (1, 1, 1, 0.2),
    "input": (0, 1, 0),
    "output": (1, 1, 1),
    }
