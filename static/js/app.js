/* Top-right user menu: click to open, click outside or press Escape to close. */
(function () {
  'use strict';

  function setupUserMenu(menu) {
    var button = menu.querySelector('[data-user-menu-button]');
    if (!button) return;

    function close() {
      menu.classList.remove('open');
      button.setAttribute('aria-expanded', 'false');
    }

    button.addEventListener('click', function (event) {
      event.stopPropagation();
      var isOpen = menu.classList.toggle('open');
      button.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', function (event) {
      if (!menu.contains(event.target)) close();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' || event.key === 'Esc') {
        if (menu.classList.contains('open')) {
          close();
          button.focus();
        }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-user-menu]').forEach(setupUserMenu);
  });
})();
