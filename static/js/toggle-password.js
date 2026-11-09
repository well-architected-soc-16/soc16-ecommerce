// Tombol tampilkan/sembunyikan password.
// Pasang atribut data-toggle-password="id-input" pada tombol.
(function () {
  document.querySelectorAll("[data-toggle-password]").forEach(function (tombol) {
    const input = document.getElementById(tombol.dataset.togglePassword);
    if (!input) return;

    tombol.addEventListener("click", function () {
      const tampil = input.type === "password";
      input.type = tampil ? "text" : "password";
      tombol.setAttribute("aria-pressed", String(tampil));
      tombol.setAttribute("aria-label", tampil ? "Sembunyikan password" : "Tampilkan password");
    });
  });

  // Kembalikan ke tersembunyi sebelum form dikirim, supaya browser tidak menyimpannya sebagai teks
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      form.querySelectorAll("[data-toggle-password]").forEach(function (tombol) {
        const input = document.getElementById(tombol.dataset.togglePassword);
        if (input) input.type = "password";
      });
    });
  });
})();