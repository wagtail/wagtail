function(modal, jsonData) {
    modal.respond('snippetChosen', jsonData['result']);
    modal.close();
}