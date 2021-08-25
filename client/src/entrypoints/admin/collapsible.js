import $ from "jquery";

function initCollapsibleBlocks() {
  // eslint-disable-next-line func-names
  $(".object.collapsible").each(function () {
    const $li = $(this);
    const $content = $li.find(".object-layout");
    const onAnimationComplete = () =>
      $content
        .get(0)
        .dispatchEvent(
          new CustomEvent("commentAnchorVisibilityChange", { bubbles: true })
        );
    if ($li.hasClass("collapsed") && $li.find(".error-message").length === 0) {
      $content.hide({
        complete: onAnimationComplete,
      });
    }

    $li.find("> .title-wrapper").on("click", () => {
      if (!$li.hasClass("collapsed")) {
        $li.addClass("collapsed");
        $content.hide({
          duration: "slow",
          complete: onAnimationComplete,
        });
      } else {
        $li.removeClass("collapsed");
        $content.show({
          duration: "slow",
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
