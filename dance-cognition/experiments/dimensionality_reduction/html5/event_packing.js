function packEvent(event) {
    return JSON.stringify(serialize(event));
}

function serialize(event) {
    return {"py/Event": {
	"type": event.type,
	"content": {"py/dict": event.content}
    }};
}
