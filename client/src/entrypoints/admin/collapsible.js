import $ from 'jquery';

function initCollapsibleBlocks() {
  // eslint-disable-next-line func-names
  $('.object.collapsible').each(function () {
    const $target = $(this);
    const $content = $target.find('.object-layout');
    const onAnimationComplete = () =>
      $content
        .get(0)
        .dispatchEvent(
          new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
        );
    if (
      $target.hasClass('collapsed') &&
      $target.find('.error-message').length === 0
    ) {
      $content.hide({
        complete: onAnimationComplete,
      });
    }

    $target.find('> .title-wrapper').on('click', () => {
      if (!$target.hasClass('collapsed')) {
        $target.addClass('collapsed');
        $content.hide({
          duration: 'slow',
          complete: onAnimationComplete,
        });
      } else {
        $target.removeClass('collapsed');
        $content.show({
          duration: 'slow',
          complete: onAnimationComplete,
        });
      }
    });
  });
}
window.initCollapsibleBlocks = initCollapsibleBlocks;

$(() => {
  initCollapsibleBlocks();
});
