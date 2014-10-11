function WebsocketClient(address, handleEvent) {
    this.ws = new WebSocket(address);
    this.ws.onmessage = function(message) {
	event = unpackEvent(message.data);
	handleEvent(event);
    }

    this.sendEvent = function(event) {
	this.ws.send(packEvent(event));
    }
}
