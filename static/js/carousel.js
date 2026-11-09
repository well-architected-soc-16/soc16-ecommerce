// Hero banner berganti otomatis di beranda.
(function () {
  const carousel = document.querySelector("[data-carousel]");
  if (!carousel) return;

  const slides = carousel.querySelectorAll("[data-slide]");
  const dots = carousel.querySelectorAll("[data-dot]");
  if (slides.length < 2) return;

  const JEDA = 5000; // ganti slide tiap 5 detik
  const tanpaAnimasi = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let aktif = 0;
  let timer = null;

  // Tampilkan tombol & titik (tanpa JS, hanya slide pertama yang terlihat)
  carousel.querySelectorAll("[data-prev], [data-next], [data-dots]").forEach((el) => (el.hidden = false));

  function tampilkan(nomor) {
    aktif = (nomor + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      const ini = i === aktif;
      slide.classList.toggle("opacity-100", ini);
      slide.classList.toggle("opacity-0", !ini);
      slide.classList.toggle("invisible", !ini);
    });
    dots.forEach((dot, i) => {
      const ini = i === aktif;
      dot.classList.toggle("bg-black", ini);
      dot.classList.toggle("bg-white", !ini);
      if (ini) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
  }

  function mulai() {
    if (tanpaAnimasi || timer) return;
    timer = setInterval(() => tampilkan(aktif + 1), JEDA);
  }

  function berhenti() {
    clearInterval(timer);
    timer = null;
  }

  carousel.querySelector("[data-prev]").addEventListener("click", () => tampilkan(aktif - 1));
  carousel.querySelector("[data-next]").addEventListener("click", () => tampilkan(aktif + 1));
  dots.forEach((dot, i) => dot.addEventListener("click", () => tampilkan(i)));

  // Berhenti saat kursor di atas banner atau tombolnya sedang difokus keyboard
  carousel.addEventListener("mouseenter", berhenti);
  carousel.addEventListener("mouseleave", mulai);
  carousel.addEventListener("focusin", berhenti);
  carousel.addEventListener("focusout", mulai);

  // Berhenti saat tab browser tidak sedang dilihat
  document.addEventListener("visibilitychange", () => (document.hidden ? berhenti() : mulai()));

  mulai();
})();