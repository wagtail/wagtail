function(modal, jsonData) {
    modal.respond('documentChosen', jsonData['result']);
    modal.close();
}
