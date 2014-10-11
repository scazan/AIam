import json
from event import Event
import numpy

class EventPacker:
    @classmethod
    def pack(cls, event):
        return json.dumps(cls._serialize(event))

    @classmethod
    def unpack(cls, string):
        return json.loads(string, object_hook=cls._restore)

    @classmethod
    def _serialize(cls, obj):
        if obj is None or isinstance(obj, (bool, int, long, float, basestring)):
            return obj
        if isinstance(obj, list):
            return [cls._serialize(val) for val in obj]
        if isinstance(obj, dict):
            return {"py/dict": dict(
                    (k, cls._serialize(v))
                    for k, v in obj.iteritems()
                    )}
        if isinstance(obj, numpy.ndarray):
            return {
                "py/numpy.ndarray": {
                    "values": obj.tolist(),
                    "dtype":  str(obj.dtype)}}
        if isinstance(obj, Event):
            return {
                "py/Event": {
                    "type": obj.type,
                    "content": cls._serialize(obj.content)}}
        raise TypeError("Type %s not obj-serializable" % type(obj))

    @classmethod
    def _restore(cls, obj):
        if not isinstance(obj, dict):
            return obj
        if "py/dict" in obj:
            return dict(obj["py/dict"])
        if "py/numpy.ndarray" in obj:
            data = obj["py/numpy.ndarray"]
            return numpy.array(data["values"], dtype=data["dtype"])
        if "py/Event" in obj:
            data = obj["py/Event"]
            return Event(data["type"], cls._restore(data["content"]))
        return obj
