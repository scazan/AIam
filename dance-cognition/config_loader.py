import imp
from states import state_machine
from vector import *

def load_config(name=None):
    if name is None:
        name = "default"
    config = imp.load_source("config", "input_data/%s/config.py" % name)
    config.center = Vector3d(*config.center)
    config.size = Vector3d(*config.size)
    state_machine.set_config(config)
    return config

