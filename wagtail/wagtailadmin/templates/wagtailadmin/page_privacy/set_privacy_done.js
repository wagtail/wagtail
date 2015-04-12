function(modal) {
    modal.respond('setPermission', '{% if is_public %}true{% endif %}' === 'true' ? true : false );
    modal.close();
}
