$(function() {
    buildExpandingFormset('id_page_permissions', {
        onInit: function(index) {
            var deleteInputId = 'id_page_permissions-' + index + '-DELETE';
            var childId = 'inline_child_page_permissions-' + index;
            $('#' + deleteInputId + '-button').on('click', function() {
                /* set 'deleted' form field to true */
                $('#' + deleteInputId).val('1');
                $('#' + childId).fadeOut();
            });
        }
    });

    // "Check all" boxes for the Group edit view.
    const toggleBoxes = document.querySelectorAll('.js-toggle-permission');
    for(let toggleBox = 0; toggleBox < toggleBoxes.length; toggleBox++) {
      const node = toggleBoxes[toggleBox];
      node.addEventListener('change', function() {
        const type = this.dataset.for;
        const selector = '.' + type + '-column input[type="checkbox"]';
        const boxes = document.querySelectorAll(selector);
        const checked = this.checked ? true : false;
          for(let i = 0; i < boxes.length; i++) {
              const element = boxes[i];
              element.checked = checked;
          }
      });
    }
});
