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
    } else {
      $(document).off('click.dropdown.cancel');
    }
  });
});

function controlbykey(event, listItems, currentIndex) {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);
  var Items = listItems;
  var prevIndex = Math.max(0, currentIndex - 1);
  var nextIndex = Math.min(listItems.length - 1, currentIndex + 1);

  // Control closes dropdown when Escape keydown
  if (event.key === 'Escape') {
    $dropdown.removeClass('open');
  }

  // Control By Arrow Up, Down, Home, End
  switch (event.key) {
  case 'ArrowUp':
    event.preventDefault();
    Items[prevIndex].firstElementChild.tabIndex = 0;
    Items[prevIndex].firstElementChild.focus();
    break;
  case 'ArrowDown':
    event.preventDefault();
    Items[nextIndex].firstElementChild.tabIndex = 0;
    Items[nextIndex].firstElementChild.focus();
    break;
  case 'Home':
    event.preventDefault();
    Items[0].firstElementChild.tabIndex = 0;
    Items[0].firstElementChild.focus();
    break;
  case 'End':
    event.preventDefault();
    Items[listItems.length - 1].firstElementChild.tabIndex = 0;
    Items[listItems.length - 1].firstElementChild.focus();
    break;
  default:
    break;
  }
}

// Invoke on: dropdown toggle button keydown
$('.dropdown-toggle').on('keydown', (e) => {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);
  const listItems = document.querySelectorAll('.dropdown li');
  const currentIndex = -1;
  e.stopPropagation();
  if ($dropdown.hasClass('open')) {
    controlbykey(e, listItems, currentIndex);
  }
});

// Invoke on: dropdown item keydown
$('.dropdown ul li a, .dropdown ul li button').on('keydown', (e) => {
  const $dropdown = $(document.querySelectorAll('.dropdown')[0]);
  const listitems = Array.prototype.slice.call(document.querySelectorAll('.dropdown li'));
  var currentIndex = listitems.indexOf(document.activeElement.parentElement);
  e.stopPropagation();
  if ($dropdown.hasClass('open')) {
    controlbykey(e, listitems, currentIndex);
  } else {
    $dropdown.toggleClass('open');
  }
});
