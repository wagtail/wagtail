// JavaScript source code
import $ from 'jquery';

$('.dropdown').each(function () {
  const $dropdown = $(this);

  $('.dropdown-toggle', $dropdown).on('click', (e) => {
    e.stopPropagation();
    $dropdown.toggleClass('open');
    if ($dropdown.hasClass('open')) {
      // If a dropdown is opened, add an event listener for document clicks to close it
      $(document).on('click.dropdown.cancel', (e2) => {
        const relTarg = e2.relatedTarget || e2.toElement;

        // Only close dropdown if the click target wasn't a child of this dropdown
        if (!$(relTarg).parents().is($dropdown)) {
          $dropdown.removeClass('open');
          $(document).off('click.dropdown.cancel');
        }
      });
    }
    else {
      $(document).off('click.dropdown.cancel');
    }
  });
});

function controlbykey(event, listItems, currentIndex) {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);

  // Control closes dropdown when Escape keydown
  if (event.key === 'Escape') {
    $dropdown.removeClass('open');
  }

  // Control By Arrow Up, Down, Home, End 
  switch (event.key) {
    case 'ArrowUp':
      var prevIndex = Math.max(0, currentIndex - 1);
      event.preventDefault();
      listItems[prevIndex].firstElementChild.tabIndex = 0;
      listItems[prevIndex].firstElementChild.focus();
      break;
    case 'ArrowDown':
      var nextIndex = Math.min(listItems.length - 1, currentIndex + 1);
      event.preventDefault();
      listItems[nextIndex].firstElementChild.tabIndex = 0;
      listItems[nextIndex].firstElementChild.focus();
      break;
    case 'Home':
      event.preventDefault();
      listItems[0].firstElementChild.tabIndex = 0;
      listItems[0].firstElementChild.focus();
      break;
    case 'End':
      event.preventDefault();
      listItems[listItems.length - 1].firstElementChild.tabIndex = 0;
      listItems[listItems.length - 1].firstElementChild.focus();
      break;
    default:
      break;
  }
}

// Invoke on: dropdown toggle button keydown
$('.dropdown-toggle').on('keydown', (e) => {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);
  const listItems = document.querySelectorAll('.dropdown li');
  e.stopPropagation();
  if ($dropdown.hasClass('open')) {
    var currentIndex = -1;
    controlbykey(e, listItems, currentIndex)
  }
});

// Invoke on: dropdown item keydown
$('.dropdown ul li a, .dropdown ul li button').on('keydown', (e) => {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);
  const listItems = Array.prototype.slice.call(document.querySelectorAll('.dropdown li'));
  var currentIndex = listItems.indexOf(document.activeElement.parentElement);
  e.stopPropagation();
  if ($dropdown.hasClass('open')) {
    controlbykey(e, listItems, currentIndex)
  }
  else {
    $dropdown.toggleClass('open');
  }
});
