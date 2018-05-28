function(modal, jsonData) {
    modal.respond('imageChosen', jsonData['result']);
    modal.close();
}
