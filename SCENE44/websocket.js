
var websocket = new WebSocket("ws://localhost:8888/ws");

// When the connection is open, send some data to the server
websocket.onopen = function () {
	console.log('websocket_ready')
};

// Log errors
websocket.onerror = function (error) {
  console.log(error);
};

// Log messages from the server
websocket.onmessage = function (e) {
  console.log(e.data);
  // if (e.eventType == "press") {
  //   triggerKeyboardPress(document.body, parseInt(e.keyCode));
  // }
  // if (e.eventType == "release") {
  //   triggerKeyboardRelease(document.body, parseInt(e.keyCode));
  // }
};

  sendSocketMsg = function(msg){
	if(websocket.readyState == 1){
    	websocket.send(msg);
  	}
	else{
    websocket.onopen = function(e){
      websocket.send(msg);
    }
	}
}