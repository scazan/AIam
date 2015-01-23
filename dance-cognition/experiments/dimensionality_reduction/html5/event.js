function Event (type, content) {
    this.type = type;
    this.content = content;
    this.source = null;
}

function PyDict (dict) {
    this.dict = dict;
}
