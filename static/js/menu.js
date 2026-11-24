// Dropdown <details data-dropdown> (Menu Akun, Menu Brand, sort_dropdown):
// tutup saat klik di luar, saat Esc, dan saat dropdown lain dibuka; aria-expanded di <summary>
// ikut diperbarui; panah atas/bawah berpindah antar tautan di panel yang terbuka; panel yang keluar
// layar digeser ke sisi sebaliknya (keepInView).
(function () {
  const menus = Array.from(document.querySelectorAll("details[data-dropdown]"));
  if (menus.length === 0) return;

  function links(menu) {
    return Array.from(menu.querySelectorAll("a[href], button:not([disabled])"))
      .filter(function (el) { return !el.closest("summary"); });
  }

  // Panel [data-dropdown-panel] yang keluar layar (mis. rata kanan tapi tombolnya di kiri pada HP)
  // dipindah ke sisi sebaliknya. Tanpa JS panel tetap tampil di posisi bawaan.
  function keepInView(menu) {
    const panel = menu.querySelector("[data-dropdown-panel]");
    if (!panel) return;
    panel.style.left = "";
    panel.style.right = "";
    const box = panel.getBoundingClientRect();
    const margin = 8;
    if (box.left < margin) {
      panel.style.left = "0";
      panel.style.right = "auto";
    } else if (box.right > window.innerWidth - margin) {
      panel.style.right = "0";
      panel.style.left = "auto";
    }
  }

  menus.forEach(function (menu) {
    const summary = menu.querySelector("summary");
    summary.setAttribute("aria-expanded", menu.open ? "true" : "false");

    menu.addEventListener("toggle", function () {
      summary.setAttribute("aria-expanded", menu.open ? "true" : "false");
      if (!menu.open) return;
      keepInView(menu);
      menus.forEach(function (lain) {
        if (lain !== menu) lain.open = false;
      });
    });

    menu.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const items = links(menu);
      if (items.length === 0) return;
      e.preventDefault();
      if (!menu.open) menu.open = true;
      const i = items.indexOf(document.activeElement);
      const next = e.key === "ArrowDown" ? (i + 1) % items.length : (i <= 0 ? items.length - 1 : i - 1);
      items[next].focus();
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
