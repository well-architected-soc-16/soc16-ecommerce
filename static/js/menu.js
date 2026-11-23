// Dropdown <details data-dropdown> (Menu Akun, Menu Brand):
// tutup saat klik di luar, saat Esc, dan saat dropdown lain dibuka.
(function () {
  const menus = Array.from(document.querySelectorAll("details[data-dropdown]"));
  if (menus.length === 0) return;

  menus.forEach(function (menu) {
    menu.addEventListener("toggle", function () {
      if (!menu.open) return;
      menus.forEach(function (lain) {
        if (lain !== menu) lain.open = false;
      });
    });
  });

  document.addEventListener("click", function (e) {
    menus.forEach(function (menu) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    menus.forEach(function (menu) {
      if (menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  });
})();
