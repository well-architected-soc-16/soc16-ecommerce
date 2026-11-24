// Detail produk: pilih ukuran -> tampilkan sisa stok dan batasi stepper jumlah; kirim ke keranjang
// tanpa ukuran -> pesan "Pilih ukuran dulu." (server tetap memeriksa ulang semuanya).
// Tanpa JS ukuran tetap bisa dipilih (radio) dan jumlah tetap bisa diketik.
(function () {
  const picker = document.querySelector("[data-size-picker]");
  const stepper = document.querySelector("[data-stepper]");
  const form = document.querySelector("[data-add-to-cart]");
  if (!picker || !stepper) return;

  const info = picker.querySelector("[data-size-info]");
  const input = stepper.querySelector("input");
  const minus = stepper.querySelector('[data-step="-1"]');
  const plus = stepper.querySelector('[data-step="1"]');
  const defaultInfo = info ? info.textContent : "";

  function limit() {
    return Math.max(1, parseInt(input.max, 10) || 1);
  }

  function clamp() {
    let value = parseInt(input.value, 10);
    if (isNaN(value) || value < 1) value = 1;
    if (value > limit()) value = limit();
    input.value = value;
    minus.disabled = input.disabled || value <= 1;
    plus.disabled = input.disabled || value >= limit();
  }

  picker.addEventListener("change", function (e) {
    const radio = e.target;
    if (radio.name !== "product_size_id") return;
    const stock = parseInt(radio.dataset.stock, 10) || 0;
    input.max = Math.max(1, stock);
    if (info) {
      info.textContent = "Sisa " + stock + " pasang untuk EU " + radio.dataset.size + " · ukuran bergaris = stok habis";
      info.classList.remove("text-red-700");
    }
    clamp();
  });

  stepper.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-step]");
    if (!btn || btn.disabled) return;
    input.value = (parseInt(input.value, 10) || 1) + parseInt(btn.dataset.step, 10);
    clamp();
  });

  if (form) {
    form.addEventListener("submit", function (e) {
      if (picker.querySelector('input[name="product_size_id"]:checked')) return;
      e.preventDefault();
      if (info) {
        info.textContent = "Pilih ukuran dulu.";
        info.classList.add("text-red-700");
      }
      const first = picker.querySelector('input[name="product_size_id"]:not(:disabled)');
      if (first) first.focus();
      picker.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  input.addEventListener("change", clamp);
  if (info) info.textContent = defaultInfo;
  clamp();
})();
