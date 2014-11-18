function WebsocketClient(address, handleEvent) {
    this.ws = new WebSocket(address);

    this.ws.onopen = function(_event) {
	console.log("WebSocket connection established");
	var event = new Event("SUBSCRIBE", ["PARAMETER"]);
	this.send(packEvent(event));
    }

    this.ws.onerror = function() {
	console.log("WebSocket.onerror");
    }

    this.ws.onclose = function(event) {
	console.log("WebSocket.onclose: " + event.reason + " (code " + event.code + ")");
    }

    this.ws.onmessage = function(message) {
	event = unpackEvent(message.data);
	handleEvent(event);
    }

    this.sendEvent = function(event) {
	this.ws.send(packEvent(event));
    }
}
