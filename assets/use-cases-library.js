(() => {
  const root = document.documentElement;
  const q = document.getElementById("uc-q");
  const pills = [...document.querySelectorAll(".uc-pill")];
  const count = document.getElementById("uc-count");
  const empty = document.getElementById("uc-empty");
  const groups = [...document.querySelectorAll(".uc-group")];
  const showAll = document.getElementById("uc-show-all");
  if (!q || !count) return;

  root.classList.add("uc-js");

  let cat = "all";
  let index = null;
  let indexPromise = null;
  let extrasBuilt = false;

  const escapeHtml = (value) =>
    String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  const loadIndex = () => {
    if (index) return Promise.resolve(index);
    if (!indexPromise) {
      indexPromise = fetch("/use-cases/search.json", { credentials: "same-origin" })
        .then((res) => {
          if (!res.ok) throw new Error("search index missing");
          return res.json();
        })
        .then((data) => {
          index = Array.isArray(data) ? data : data.items || [];
          return index;
        });
    }
    return indexPromise;
  };

  const cardHTML = (item, showCat) => {
    const note = item.n ? `\n              <p class="uc-card-note">${escapeHtml(item.n)}</p>` : "";
    const catLabel = showCat && item.l ? `<span class="uc-card-cat">${escapeHtml(item.l)}</span>` : "";
    return `<li class="uc-card" data-cat="${escapeHtml(item.c)}" data-slug="${escapeHtml(item.s)}">
            <a href="${escapeHtml(item.s)}/">
              ${catLabel}
              <h3>${escapeHtml(item.t)}</h3>
              <p>${escapeHtml(item.u)}</p>${note}
              <span class="uc-card-more">Read the use case <span aria-hidden="true">→</span></span>
            </a>
          </li>`;
  };

  const ensureExtraCards = () => {
    if (extrasBuilt || !index) return;
    extrasBuilt = true;
    const byCat = new Map();
    index.forEach((item) => {
      if (!byCat.has(item.c)) byCat.set(item.c, []);
      byCat.get(item.c).push(item);
    });
    groups.forEach((group) => {
      const slug = group.getAttribute("data-group");
      const grid = group.querySelector(".uc-grid");
      const compact = group.querySelector(".uc-index");
      if (!grid) return;
      const have = new Set(
        [...grid.querySelectorAll("[data-slug]")].map((node) => node.getAttribute("data-slug"))
      );
      const extras = (byCat.get(slug) || []).filter((item) => !have.has(item.s));
      if (!extras.length) {
        if (compact) compact.remove();
        return;
      }
      grid.insertAdjacentHTML("beforeend", extras.map((item) => cardHTML(item, false)).join(""));
      if (compact) compact.remove();
    });
  };

  const apply = () => {
    const terms = q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const filtering = terms.length > 0 || cat !== "all";
    const cards = [...document.querySelectorAll(".uc-card")];
    const compactItems = [...document.querySelectorAll(".uc-compact")];
    let shown = 0;

    const hayFor = (slug) => {
      if (!index) return "";
      const row = index.find((item) => item.s === slug);
      return row ? row.h : "";
    };

    const match = (node) => {
      const okCat = cat === "all" || node.dataset.cat === cat;
      if (!okCat) return false;
      if (!terms.length) return true;
      const hay = (node.dataset.hay || hayFor(node.dataset.slug) || node.textContent || "").toLowerCase();
      return terms.every((term) => hay.includes(term));
    };

    cards.forEach((card) => {
      const ok = match(card);
      const extra = card.classList.contains("uc-extra");
      const group = card.closest(".uc-group");
      const groupOpen = group && group.classList.contains("is-open");
      const visible = ok && (!extra || filtering || extrasBuilt || groupOpen);
      card.hidden = !visible;
      if (visible) shown += 1;
    });
    compactItems.forEach((item) => {
      const ok = match(item);
      const group = item.closest(".uc-group");
      const groupOpen = group && group.classList.contains("is-open");
      const visible = ok && (filtering || extrasBuilt || groupOpen);
      item.hidden = !visible;
      if (visible) shown += 1;
    });

    groups.forEach((group) => {
      const vis =
        group.querySelectorAll(".uc-card:not([hidden])").length +
        group.querySelectorAll(".uc-compact:not([hidden])").length;
      group.hidden = vis === 0;
      const btn = group.querySelector(".uc-more");
      group.classList.toggle("is-open", filtering || extrasBuilt || (btn && btn.getAttribute("aria-expanded") === "true"));
      if (btn) btn.hidden = filtering || extrasBuilt;
    });

    if (showAll) showAll.hidden = filtering || extrasBuilt;
    const total = index ? index.length : cards.length + compactItems.length;
    count.textContent = "Showing " + shown + " of " + total + " use cases";
    if (empty) empty.hidden = shown > 0;
  };

  const openAll = () => {
    groups.forEach((group) => {
      group.classList.add("is-open");
      const btn = group.querySelector(".uc-more");
      if (btn) {
        btn.setAttribute("aria-expanded", "true");
        btn.hidden = true;
      }
    });
    if (showAll) showAll.hidden = true;
  };

  groups.forEach((group) => {
    const btn = group.querySelector(".uc-more");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.textContent = open ? "Show fewer" : "Show all " + btn.dataset.n;
      group.classList.toggle("is-open", open);
      if (open) {
        loadIndex()
          .then(() => {
            ensureExtraCards();
            apply();
          })
          .catch(() => apply());
      }
    });
  });

  if (showAll) {
    showAll.addEventListener("click", () => {
      loadIndex()
        .then(() => {
          ensureExtraCards();
          openAll();
          apply();
        })
        .catch(() => {
          openAll();
          apply();
        });
    });
  }

  pills.forEach((pill) =>
    pill.addEventListener("click", () => {
      cat = pill.dataset.filter;
      pills.forEach((other) => {
        const on = other === pill;
        other.classList.toggle("is-active", on);
        other.setAttribute("aria-pressed", on ? "true" : "false");
      });
      const needIndex = cat !== "all" || q.value.trim().length > 0;
      if (needIndex) {
        loadIndex()
          .then(() => {
            ensureExtraCards();
            apply();
          })
          .catch(() => apply());
      } else {
        apply();
      }
    })
  );

  q.addEventListener("input", () => {
    if (q.value.trim()) {
      loadIndex()
        .then(() => {
          ensureExtraCards();
          apply();
        })
        .catch(() => apply());
    } else {
      apply();
    }
  });
})();
