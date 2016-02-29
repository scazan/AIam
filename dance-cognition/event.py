class Event:
    SUBSCRIBE = "SUBSCRIBE"
    START = "START"
    STOP = "STOP"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    REDUCTION = "REDUCTION"
    PARAMETER = "PARAMETER"
    SET_CURSOR = "SET_CURSOR"
    IMPROVISE_PATH = "IMPROVISE_PATH"
    MODE = "MODE"
    CURSOR = "CURSOR"
    VELOCITY = "VELOCITY"
    START_EXPORT_BVH = "START_EXPORT_BVH"
    STOP_EXPORT_BVH = "STOP_EXPORT_BVH"
    BVH_INDEX = "BVH_INDEX"
    PROCEED_TO_NEXT_FRAME = "PROCEED_TO_NEXT_FRAME"
    ABORT_PATH = "ABORT_PATH"
    FEATURES = "FEATURES"
    TARGET_FEATURES = "TARGET_FEATURES"
    FEATURE_MATCH_RESULT = "FEATURE_MATCH_RESULT"
    TARGET_ROOT_Y_ORIENTATION = "TARGET_ROOT_Y_ORIENTATION"

    def __init__(self, type_, content=None):
        self.type = type_
        self.content = content
        self.source = None

    def __str__(self):
        return "Event(%r, %r, source=%s)" % (self.type, self.content, self.source)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.type == other.type and self.content == other.content

    def __ne__(self, other):
        return not (self == other)

    def __getstate__(self):
        return (self.type, self.content)

    def __setstate__(self, state):
        self.type, self.content = state
