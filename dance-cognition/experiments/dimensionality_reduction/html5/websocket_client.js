function WebsocketClient(address, handleConnected, handleEvent, handleError) {
    this.ws = new WebSocket(address);

    this.ws.onopen = function(_event) {
	console.log("WebSocket connection established");
	var event = new Event("REGISTER_REMOTE_UI", []);
	this.send(packEvent(event));
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
	this.ws.send(packEvent(event));
    }
}
