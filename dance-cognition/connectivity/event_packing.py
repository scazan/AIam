import cPickle

class EventPacker:
    @staticmethod
    def pack(event):
        return cPickle.dumps(event)

    @staticmethod
    def unpack(string):
        return cPickle.loads(string)
