
var websocket = new WebSocket("ws://localhost:8888/ws");

  data=1;
  var _this = this;

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
    // console.log(e.data);

    data = JSON.parse(e.data)
    
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


 