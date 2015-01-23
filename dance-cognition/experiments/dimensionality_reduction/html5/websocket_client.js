function WebsocketClient(ownerName, address, handleConnected, handleEvent, handleError) {
    this.ws = new WebSocket(address);

    this.ws.onopen = function(_event) {
	console.log("WebSocket connection established");
	this.send(packEvent(new Event("REGISTER", ownerName)));
	this.send(packEvent(new Event("REGISTER_REMOTE_UI", [])));
	handleConnected();
    }

    this.ws.onerror = function() {
	console.log("WebSocket.onerror");
	handleError("connection error");
    }

    this.ws.onclose = function(event) {
	console.log("WebSocket.onclose: " + event.reason + " (code " + event.code + ")");
	handleError("connection closed " + event.reason + " (code " + event.code + ")");
    }

    this.ws.onmessage = function(message) {
	event = unpackEvent(message.data);
	handleEvent(event);
    }

    this.sendEvent = function(event) {
	event.source = ownerName;
	this.ws.send(packEvent(event));
    }
}
