class Event:
    START = "START"
    STOP = "STOP"
    OUTPUT = "OUTPUT"
    REDUCTION = "REDUCTION"
    PARAMETER = "PARAMETER"
    SET_CURSOR = "SET_CURSOR"
    IMPROVISER_PATH = "IMPROVISER_PATH"
    MODE = "MODE"

    def __init__(self, type_, content=None):
        self.type = type_
        self.content = content

    def __str__(self):
        return "Event(%r, %r)" % (self.type, self.content)
