function(modal, jsonData) {
    modal.respond('setPermission', jsonData['is_public']);
    modal.close();
}
