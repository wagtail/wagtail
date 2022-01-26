import $ from 'jquery';

function makeHalloRichTextEditable(id, plugins) {
  const input = $('#' + id);
  const editor = $('<div class="halloeditor" data-hallo-editor></div>').html(input.val());
  editor.insertBefore(input);
  input.hide();

  let removeStylingPending = false;
  function removeStyling() {
    /* Strip the 'style' attribute from spans that have no other attributes.
    (we don't remove the span entirely as that messes with the cursor position,
    and spans will be removed anyway by our whitelisting)
    */
    // eslint-disable-next-line func-names
    $('span[style]', editor).filter(function () {
      return this.attributes.length === 1;
    }).removeAttr('style');
    removeStylingPending = false;
  }

  /* Workaround for faulty change-detection in hallo */
  function setModified() {
    const hallo = editor.data('IKS-hallo');
    if (hallo) {
      hallo.setModified();
    }
  }

  const closestObj = input.closest('.object');

  editor.hallo({
    toolbar: 'halloToolbarFixed',
    toolbarCssClass: (closestObj.hasClass('full')) ? 'full' : '',
    /* use the passed-in plugins arg */
    plugins: plugins
  }).on('hallomodified', (event, data) => {
    input.val(data.content);
    if (!removeStylingPending) {
      setTimeout(removeStyling, 100);
      removeStylingPending = true;
    }
  }).on('paste drop', () => {
    setTimeout(() => {
      removeStyling();
      setModified();
    }, 1);
  /* Animate the fields open when you click into them. */
  })
    .on('halloactivated', (event) => {
      $(event.target).addClass('expanded', 200, () => {
      /* Hallo's toolbar will reposition itself on the scroll event.
      This is useful since animating the fields can cause it to be
      positioned badly initially. */
        $(window).trigger('scroll');
      });
    })
    .on('hallodeactivated', (event) => {
      $(event.target).removeClass('expanded', 200, () => {
        $(window).trigger('scroll');
      });
    });

  // eslint-disable-next-line @typescript-eslint/no-use-before-define
  setupLinkTooltips(editor);
}
window.makeHalloRichTextEditable = makeHalloRichTextEditable;

function setupLinkTooltips(elem) {
  elem.tooltip({
    animation: false,
    title() {
      return $(this).attr('href');
    },
    trigger: 'hover',
    placement: 'bottom',
    selector: 'a'
  });
}
window.setupLinkTooltips = setupLinkTooltips;

function insertRichTextDeleteControl(elem) {
  const anchor = $('<a class="icon icon-cross text-replace halloembed__delete">Delete</a>');
  $(elem).addClass('halloembed').prepend(anchor);
  anchor.on('click', () => {
    const widget = $(elem).parent('[data-hallo-editor]').data('IKS-hallo');
    $(elem).fadeOut(() => {
      $(elem).remove();
      if (widget !== undefined && widget.options.editable) {
        widget.element.trigger('change');
      }
    });
  });
}
window.insertRichTextDeleteControl = insertRichTextDeleteControl;

$(() => {
  // eslint-disable-next-line func-names
  $('[data-hallo-editor] [contenteditable="false"]').each(function () {
    insertRichTextDeleteControl(this);
  });
});
