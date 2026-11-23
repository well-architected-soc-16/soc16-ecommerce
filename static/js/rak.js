// Rak produk geser di beranda (macro product_shelf).
// Tanpa JS rak tetap bisa digeser (overflow-x); tombol ‹ › hanya muncul di layar >= 768px
// dan disembunyikan saat rak sudah di ujung kiri/kanan.
(function () {
  const desktop = window.matchMedia("(min-width: 768px)");

  document.querySelectorAll("[data-shelf]").forEach(function (shelf) {
    const track = shelf.querySelector("[data-shelf-track]");
    const prev = shelf.querySelector("[data-shelf-prev]");
    const next = shelf.querySelector("[data-shelf-next]");
    if (!track || !prev || !next) return;

    function tampil(tombol, ya) {
      tombol.classList.toggle("hidden", !ya);
      tombol.classList.toggle("flex", ya);
    }

    function perbarui() {
      const sisaKanan = track.scrollWidth - track.clientWidth - track.scrollLeft;
      tampil(prev, desktop.matches && track.scrollLeft > 1);
      tampil(next, desktop.matches && sisaKanan > 1);
    }

    function geser(arah) {
      // Geser sebanyak kartu yang terlihat penuh (kartu 224px + gap 16px)
      const langkah = Math.max(240, Math.floor(track.clientWidth / 240) * 240);
      track.scrollBy({ left: arah * langkah, behavior: "smooth" });
    }

    prev.addEventListener("click", function () { geser(-1); });
    next.addEventListener("click", function () { geser(1); });
    track.addEventListener("scroll", perbarui, { passive: true });
    window.addEventListener("resize", perbarui);
    desktop.addEventListener("change", perbarui);
    perbarui();
  });
})();
