document.addEventListener('DOMContentLoaded', () => {
  const dialog = document.getElementById('schedule-publishing-dialog');

  dialog.addEventListener('hide', () => {
    const goLiveAt = document.getElementById('id_go_live_at');
    const expireAt = document.getElementById('id_expire_at');
    goLiveAt.value = goLiveAt.defaultValue;
    expireAt.value = expireAt.defaultValue;
  });
});
