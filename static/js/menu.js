(function () {
  const menu = document.getElementById("menu-profil");
  if (!menu) return;

  document.addEventListener("click", function (e) {
    if (menu.open && !menu.contains(e.target)) menu.open = false;
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") menu.open = false;
  });
})();