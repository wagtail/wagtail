import $ from 'jquery';

$.widget('IKS.hallowagtaillink', {
  options: {
    uuid: '',
    editable: null
  },
  populateToolbar(toolbar) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const widget = this;
    // eslint-disable-next-line func-names
    const getEnclosingLink = function () {
      const node = widget.options.editable.getSelection().commonAncestorContainer;
      return $(node).parents('a').get(0);
    };

    const buttonSet = $('<span class="' + this.widgetName + '"></span>');

    let addButton = $('<span></span>');
    addButton = addButton.hallobutton({
      uuid: widget.options.uuid,
      editable: widget.options.editable,
      label: 'Add/Edit Link',
      icon: 'icon-link',
      command: null,
      queryState() {
        return addButton.hallobutton('checked', !!getEnclosingLink());
      }
    });
    addButton.on('click', () => {
      let href;
      let linkType;
      let parentPageId;

      // Defaults.
      let url = window.chooserUrls.pageChooser;
      const urlParams = {
        allow_external_link: true,
        allow_email_link: true,
        allow_phone_link: true,
        allow_anchor_link: true,
      };

      const enclosingLink = getEnclosingLink();
      const lastSelection = widget.options.editable.getSelection();

      if (enclosingLink) {
        href = enclosingLink.getAttribute('href');
        parentPageId = enclosingLink.getAttribute('data-parent-id');
        linkType = enclosingLink.getAttribute('data-linktype');

        urlParams.link_text = enclosingLink.innerText;

        if (linkType === 'page' && parentPageId) {
          url = window.chooserUrls.pageChooser + parentPageId.toString() + '/';
        } else if (href.startsWith('mailto:')) {
          url = window.chooserUrls.emailLinkChooser;
          href = href.replace('mailto:', '');
          urlParams.link_url = href;
        } else if (href.startsWith('tel:')) {
          url = window.chooserUrls.phoneLinkChooser;
          href = href.replace('tel:', '');
          urlParams.link_url = href;
        } else if (href.startsWith('#')) {
          url = window.chooserUrls.anchorLinkChooser;
          href = href.replace('#', '');
          urlParams.link_url = href;
        } else if (!linkType) {  /* external link */
          url = window.chooserUrls.externalLinkChooser;
          urlParams.link_url = href;
        }
      } else if (!lastSelection.collapsed) {
        urlParams.link_text = lastSelection.toString();
      }

      // eslint-disable-next-line no-undef, new-cap
      return ModalWorkflow({
        url: url,
        urlParams: urlParams,
        // eslint-disable-next-line no-undef
        onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          pageChosen(pageData) {
            let anchor;
            let linkHasExistingContent;

            if (enclosingLink) {
              // Editing an existing link
              anchor = enclosingLink;
              linkHasExistingContent = true;
            } else if (!lastSelection.collapsed) {
              // Turning a selection into a link

              anchor = document.createElement('a');
              lastSelection.surroundContents(anchor);

              // unlink all previously existing links in the selection,
              // now nested within 'a'
              // eslint-disable-next-line func-names
              $('a[href]', anchor).each(function () {
                const parent = this.parentNode;
                while (this.firstChild) parent.insertBefore(this.firstChild, this);
                parent.removeChild(this);
              });

              linkHasExistingContent = true;
            } else {
              // Inserting a new link at the cursor position
              anchor = document.createElement('a');
              lastSelection.insertNode(anchor);
              linkHasExistingContent = false;
            }

            // Set link attributes
            anchor.setAttribute('href', pageData.url);
            if (pageData.id) {
              anchor.setAttribute('data-id', pageData.id);
              anchor.setAttribute('data-parent-id', pageData.parentId);
              anchor.setAttribute('data-linktype', 'page');
            } else {
              anchor.removeAttribute('data-id');
              anchor.removeAttribute('data-parent-id');
              anchor.removeAttribute('data-linktype');
            }

            if (pageData.prefer_this_title_as_link_text || !linkHasExistingContent) {
              // overwrite existing link content with the returned 'title' text
              anchor.innerText = pageData.title;
            }

            return widget.options.editable.element.trigger('change');
          }
        }
      });
    });
    buttonSet.append(addButton);

    let cancelButton = $('<span></span>');
    cancelButton = cancelButton.hallobutton({
      uuid: widget.options.uuid,
      editable: widget.options.editable,
      label: 'Remove Link',
      icon: 'icon-chain-broken',
      command: null,
      queryState() {
        if (!!getEnclosingLink()) {
          return cancelButton.hallobutton('enable');
        }
        return cancelButton.hallobutton('disable');
      }
    });
    cancelButton.on('click', () => {
      var enclosingLink; var sel; var
        range;

      enclosingLink = getEnclosingLink();
      if (enclosingLink) {
        // eslint-disable-next-line no-undef
        sel = rangy.getSelection();
        range = sel.getRangeAt(0);

        range.setStartBefore(sel.anchorNode.parentNode);
        range.setEndAfter(sel.anchorNode.parentNode);

        sel.setSingleRange(range, false);

        document.execCommand('unlink');
        widget.options.editable.element.trigger('change');
      }
    });
    buttonSet.append(cancelButton);

    buttonSet.hallobuttonset();
    toolbar.append(buttonSet);
  }
});
