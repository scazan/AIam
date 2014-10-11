function WebsocketClient(address) {
    this.ws = new WebSocket(address);

    this.connect = function() {
	this.ws.connect();
	this.onmessage = this.handleMessage;
    }

    this.handleMessage = function(message) {
	// console.log("handleMessage: " + message.data);
	// event = jsonToEvent(message.data);
	// handleEvent(event);
    }

    this.sendEvent = function(event) {
	this.ws.send(packEvent(event));
    }
}
