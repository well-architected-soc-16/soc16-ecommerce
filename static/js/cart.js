// Keranjang: angka jumlah yang diketik langsung dikirim (aksi=set) saat isian berubah.
// Tombol – / + sudah berupa tombol submit biasa, jadi tanpa JS tetap jalan (Enter juga mengirim aksi=set).
(function () {
  document.querySelectorAll("[data-stepper-submit] input").forEach(function (input) {
    const start = input.value;
    input.addEventListener("change", function () {
      if (input.value === start || !input.form) return;
      const set = input.form.querySelector('button[name="aksi"][value="set"]');
      if (set) input.form.requestSubmit(set);
    });
  });
})();
