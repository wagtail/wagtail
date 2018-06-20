function(modal, jsonData) {
    modal.respond('pageChosen', jsonData['result']);
    modal.close();
}
