var backendConnection;

function connectToBackend() {
    var host = getQueryStringParameter("host", "localhost");
    var port = getQueryStringParameter("port", "15001");
    var backendURL = "ws://" + host + ":" + port + "/aiam";

    backendConnection = new WebSocket(backendURL);
    backendConnection.onmessage = handleMessage;
}

function handleMessage(message) {
    // console.log("handleMessage: " + message.data);
    // event = jsonToEvent(message.data);
    // handleEvent(event);
}

function getQueryStringParameter(name, defaultValue) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? defaultValue : decodeURIComponent(results[1].replace(/\+/g, " "));
}
