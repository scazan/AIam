var client;

function connectToBackend() {
    var host = getQueryStringParameter("host", "localhost");
    var port = getQueryStringParameter("port", "15001");
    var backendURL = "ws://" + host + ":" + port + "/aiam";

    client = new WebsocketClient(backendURL, handleEvent);
}

function handleEvent(event) {
    if(event && event.type == "PARAMETER") {
	if(event.content.name == "novelty") {
	    $("#slider").slider("value", event.content.value);
	}
    }
}

function getQueryStringParameter(name, defaultValue) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? defaultValue : decodeURIComponent(results[1].replace(/\+/g, " "));
}

$(function() {
    $("#slider").slider({
	min: 0,
	max: 1,
	step: 0.001,
	slide: function(event, ui) {
            if (event.originalEvent) {
		client.sendEvent(new Event("PARAMETER", {
		    "name": "novelty",
		    "value": ui.value
		}));
            }
	}
    });
});

connectToBackend();
