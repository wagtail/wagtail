function(modal) {
    modal.respond('setPermission', '{% if is_public %}true{% endif %}' === 'true');
    modal.close();
}
