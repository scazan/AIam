function packEvent(event) {
    return JSON.stringify(serialize(event));
}

function serialize(event) {
    if(event.content instanceof PyDict)
	content = {"py/dict": event.content.dict};
    else
	content = event.content;

    return {"py/Event": {
	"type": event.type,
	"content": content,
	"source": event.source
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
