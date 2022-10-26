import $ from "jquery";

/* generic function for adding a message to message area through JS alone */
function addMessage(status: any, text:any) {
    $('.messages')
      .addClass('new')
      .empty()
      .append('<ul><li class="' + status + '">' + text + '</li></ul>');
    const addMsgTimeout = setTimeout(() => {
      $('.messages').addClass('appear');
      clearTimeout(addMsgTimeout);
    }, 100);
  }