function(modal) {
    modal.respond('imageChosen', {{ image_json|safe }});
    modal.close();
}
