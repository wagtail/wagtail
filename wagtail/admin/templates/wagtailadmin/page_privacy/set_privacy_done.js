function(modal) {
    modal.respond('setPermission', {% if is_public %}true{% else %}false{% endif %});
    modal.close();
}
