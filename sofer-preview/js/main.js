(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.body.classList.add("js-ready");

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");

  function setNav(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    nav.classList.toggle("is-open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setNav(toggle.getAttribute("aria-expanded") !== "true");
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setNav(false);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setNav(false);
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth >= 1200) setNav(false);
    });
  }

  if (!reduce && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    document.querySelectorAll(".reveal-on-scroll").forEach(function (el) {
      observer.observe(el);
    });
    window.setTimeout(function () {
      document.querySelectorAll(".reveal-on-scroll").forEach(function (el) {
        el.classList.add("is-in");
      });
    }, 2500);
  } else {
    document.querySelectorAll(".reveal-on-scroll").forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  var form = document.getElementById("contact-form");
  var status = document.getElementById("form-status");
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      // TODO: Wire this form to a real handler (Formspree, Netlify Forms, or the studio's existing mail script).
      // Do not POST anywhere until that endpoint exists.
      if (status) {
        status.textContent =
          "This design preview does not send messages yet. Please call 305-770-3481 or email info@soferonsite.com.";
        status.classList.add("is-visible");
      }
    });
  }
})();
