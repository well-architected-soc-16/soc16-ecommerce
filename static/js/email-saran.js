(function () {
  // Tambahkan domain kampusmu di sini, misalnya "students.namakampus.ac.id"
  const DOMAIN = [
    "gmail.com",
    "yahoo.com",
    "yahoo.co.id",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
  ];

  const input = document.getElementById("email");
  if (!input) return;

  input.setAttribute("autocomplete", "off");
  input.parentElement.style.position = "relative";

  const kotak = document.createElement("ul");
  Object.assign(kotak.style, {
    position: "absolute",
    top: "100%",
    left: "0",
    right: "0",
    zIndex: "10",
    background: "#fff",
    border: "1px solid #e5e5e5",
    borderRadius: "12px",
    marginTop: "0.25rem",
    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
    display: "none",
    listStyle: "none",
    padding: "0",
  });
  input.insertAdjacentElement("afterend", kotak);

  function tutup() {
    kotak.style.display = "none";
    kotak.replaceChildren();
  }

  input.addEventListener("input", function () {
    tutup();

    const nilai = input.value;
    const posisiAt = nilai.indexOf("@");
    if (posisiAt < 1) return;

    const namaDepan = nilai.slice(0, posisiAt);
    const domainDiketik = nilai.slice(posisiAt + 1).toLowerCase();
    const cocok = DOMAIN.filter(
      (d) => d.startsWith(domainDiketik) && d !== domainDiketik
    );
    if (cocok.length === 0) return;

    cocok.forEach((d) => {
      const item = document.createElement("li");
      item.textContent = namaDepan + "@" + d;
      Object.assign(item.style, { padding: "0.5rem 0.75rem", cursor: "pointer", color: "#1D2128" });

      item.addEventListener("mouseenter", () => (item.style.background = "#f5f5f5"));
      item.addEventListener("mouseleave", () => (item.style.background = ""));
      item.addEventListener("mousedown", function (e) {
        e.preventDefault();
        input.value = item.textContent;
        tutup();
      });

      kotak.appendChild(item);
    });

    kotak.style.display = "block";
  });

  input.addEventListener("blur", tutup);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") tutup();
  });
})();