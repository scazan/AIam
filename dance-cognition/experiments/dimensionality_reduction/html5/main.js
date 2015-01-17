var client;
var errorMessages = "";

function connectToBackend() {
    var host = getQueryStringParameter("host", "localhost");
    var port = getQueryStringParameter("port", "15001");
    var backendURL = "ws://" + host + ":" + port + "/aiam";

    client = new WebsocketClient(
	backendURL, handleConnected, handleEvent, handleWebsocketError);
}

function handleConnected() {
    $("#logo").css("display", "inline");
    $("#error").css("display", "none");
}

function handleEvent(event) {
    if(event && event.type == "PARAMETER") {
	var slider = $("#slider_" + event.content.name);
	if(slider) {
	    slider.slider("value", event.content.value);
	}
    }
}

function handleWebsocketError(errorMessage) {
    errorMessages += errorMessage + "<br>";
    $("#logo").css("display", "none");
    $("#error").html(errorMessages);
    $("#error").css("display", "inline");
}

function getQueryStringParameter(name, defaultValue) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? defaultValue : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function setUpSlider(name, min, max, value) {
    $("#slider_" + name).slider({
	min: min,
	max: max,
	step: 0.001,
    value: value,
    orientation: "horizontal",
    //animate: true,
    range:"min",
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

function applyStylesheet() {
    var stylesheet = getQueryStringParameter("stylesheet", "ui")
    $('head').append('<link rel="stylesheet" href="' + stylesheet + '.css" type="text/css" />');
}

$(function() {
    applyStylesheet();
    setUpSlider("novelty", 0, 1, .5);
    setUpSlider("preferred_distance", 0, 2, 1);
    setUpSlider("velocity", 0.1, 0.9, 0.5);
    connectToBackend();
});
