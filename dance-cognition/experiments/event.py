class Event:
    REGISTER = "REGISTER"
    SUBSCRIBE = "SUBSCRIBE"
    REGISTER_REMOTE_UI = "REGISTER_REMOTE_UI"
    START = "START"
    STOP = "STOP"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    REDUCTION = "REDUCTION"
    PARAMETER = "PARAMETER"
    SET_CURSOR = "SET_CURSOR"
    IMPROVISER_PATH = "IMPROVISER_PATH"
    MODE = "MODE"
    CURSOR = "CURSOR"
    VELOCITY = "VELOCITY"
    START_EXPORT_OUTPUT = "START_EXPORT_OUTPUT"
    STOP_EXPORT_OUTPUT = "STOP_EXPORT_OUTPUT"

    def __init__(self, type_, content=None):
        self.type = type_
        self.content = content
        self.source = None

    def __str__(self):
        return "Event(%r, %r, %r)" % (self.type, self.content, self.source)

    def __eq__(self, other):
        return self.type == other.type and self.content == other.content

    def __ne__(self, other):
        return not (self == other)
