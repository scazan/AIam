function WebsocketClient(address, handleEvent) {
    this.ws = new WebSocket(address);

    this.ws.onopen = function(_event) {
	var event = new Event("SUBSCRIBE", ["PARAMETER"]);
	this.send(packEvent(event));
    }

    this.ws.onmessage = function(message) {
	event = unpackEvent(message.data);
	handleEvent(event);
    }

    this.sendEvent = function(event) {
	this.ws.send(packEvent(event));
    }
}
