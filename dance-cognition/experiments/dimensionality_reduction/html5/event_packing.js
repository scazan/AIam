function packEvent(event) {
    return JSON.stringify(serialize(event));
}

function serialize(event) {
    return {"py/Event": {
	"type": event.type,
	"content": {"py/dict": event.content}
    }};
}

function unpackEvent(string) {
    return unserialize(JSON.parse(string));
}

function unserialize(obj) {
    var eventObj = obj["py/Event"];
    if(eventObj) {
	var type = eventObj.type;
    	if(type == "PARAMETER") {
    	    var content = eventObj.content["py/dict"];
	    return new Event(type, content);
    	}
    }
}
