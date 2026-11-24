// Detail produk: pilih ukuran -> tampilkan sisa stok dan batasi stepper jumlah.
// Tanpa JS ukuran tetap bisa dipilih (radio) dan jumlah tetap bisa diketik.
(function () {
  const picker = document.querySelector("[data-size-picker]");
  const stepper = document.querySelector("[data-stepper]");
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
    if (radio.name !== "size") return;
    const stock = parseInt(radio.dataset.stock, 10) || 0;
    input.max = Math.max(1, stock);
    if (info) info.textContent = "Sisa " + stock + " pasang untuk EU " + radio.value + " · ukuran bergaris = stok habis";
    clamp();
  });

  stepper.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-step]");
    if (!btn || btn.disabled) return;
    input.value = (parseInt(input.value, 10) || 1) + parseInt(btn.dataset.step, 10);
    clamp();
  });

  input.addEventListener("change", clamp);
  if (info) info.textContent = defaultInfo;
  clamp();
})();
