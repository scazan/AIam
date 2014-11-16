var client;

function connectToBackend() {
    var host = getQueryStringParameter("host", "localhost");
    var port = getQueryStringParameter("port", "15001");
    var backendURL = "ws://" + host + ":" + port + "/aiam";

    client = new WebsocketClient(backendURL, handleEvent);
}

function handleEvent(event) {
    if(event && event.type == "PARAMETER") {
	var slider = $("#slider_" + event.content.name);
	if(slider) {
	    slider.slider("value", event.content.value);
	}
    }
}

function getQueryStringParameter(name, defaultValue) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? defaultValue : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function setUpSlider(name, min, max) {
    $("#slider_" + name).slider({
	min: min,
	max: max,
	step: 0.001,
	slide: function(event, ui) {
            if (event.originalEvent) {
		client.sendEvent(new Event("PARAMETER", new PyDict({
		    "name": name,
		    "value": ui.value
		})));
            }
	}
    });
}

$(function() {
    setUpSlider("novelty", 0, 1);
    setUpSlider("preferred_distance", 0, 2);
    setUpSlider("velocity", 0.1, 3);
    connectToBackend();
});
