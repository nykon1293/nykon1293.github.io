(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  const nav = document.querySelector(".nav");
  const toggle = document.querySelector(".nav-toggle");
  const links = document.getElementById("site-nav");
  if (!nav || !toggle || !links) return;

  const setOpen = (open) => {
    nav.classList.toggle("is-menu-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close site menu" : "Open site menu");
  };

  toggle.addEventListener("click", () => setOpen(!nav.classList.contains("is-menu-open")));
  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      setOpen(false);
      links.querySelectorAll("details.nav-dropdown[open]").forEach((d) => d.removeAttribute("open"));
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
  document.addEventListener("click", (event) => {
    if (!nav.classList.contains("is-menu-open")) return;
    if (nav.contains(event.target)) return;
    setOpen(false);
  });
})();
