function(modal, jsonData) {
    modal.respond('embedChosen', jsonData['embed_html'], jsonData['embed_data']);
    modal.close();
}
