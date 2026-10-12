(() => {
  const root = document.documentElement;
  const body = document.body;
  const mode = body.dataset.uc || "hub";
  const pageSlug = body.dataset.ucSlug || "";
  const lazy = body.dataset.ucLazy === "1";
  const q = document.getElementById("uc-q");
  const count = document.getElementById("uc-count");
  const empty = document.getElementById("uc-empty");
  const grid = document.getElementById("uc-grid");
  const showMore = document.getElementById("uc-show-more");
  const clearBtn = document.getElementById("uc-clear");
  const moreFilters = document.getElementById("uc-more-filters");
  const configEl = document.getElementById("uc-config");
  const config = configEl ? JSON.parse(configEl.textContent || "{}") : {};
  const PAGE = config.page || 18;
  const TOTAL = config.n || 0;
  const legacy = config.legacy || {};

  const hash = (location.hash || "").replace(/^#/, "");
  if (hash && legacy[hash]) {
    location.replace(legacy[hash]);
    return;
  }

  if (moreFilters) {
    const summary = moreFilters.querySelector("summary");
    const sync = () => {
      if (summary) summary.setAttribute("aria-expanded", moreFilters.open ? "true" : "false");
    };
    sync();
    moreFilters.addEventListener("toggle", sync);
  }

  root.classList.add("uc-js");

  let index = null;
  let indexPromise = null;
  let industries = [];
  let functions = [];
  let pageSize = mode === "hub" ? 12 : 12;

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
          const payload = data && typeof data === "object" ? data : {};
          if (payload.legacy && !Object.keys(legacy).length) {
            Object.assign(legacy, payload.legacy);
          }
          index = Array.isArray(data) ? data : payload.items || [];
          return index;
        });
    }
    return indexPromise;
  };

  const cardHTML = (item) => {
    const note = item.n ? `\n              <p class="uc-card-note">${escapeHtml(item.n)}</p>` : "";
    const label = item.l ? `<span class="uc-card-cat">${escapeHtml(item.l)}</span>` : "";
    const i = (item.i || []).join(",");
    const f = (item.f || []).join(",");
    return `<li class="uc-card uc-injected" data-slug="${escapeHtml(item.s)}" data-i="${escapeHtml(i)}" data-f="${escapeHtml(f)}">
            <a href="/use-cases/${escapeHtml(item.s)}/">
              ${label}
              <h3>${escapeHtml(item.t)}</h3>
              <p>${escapeHtml(item.u)}</p>${note}
              <span class="uc-card-more">Read the use case <span aria-hidden="true">→</span></span>
            </a>
          </li>`;
  };

  const terms = () => (q ? q.value.trim().toLowerCase().split(/\s+/).filter(Boolean) : []);

  const filtering = () => terms().length > 0 || industries.length > 0 || functions.length > 0;

  const matches = (item) => {
    if (mode === "industry" && pageSlug && !(item.i || []).includes(pageSlug)) return false;
    if (mode === "function" && pageSlug && !(item.f || []).includes(pageSlug)) return false;
    const okI = !industries.length || industries.some((slug) => (item.i || []).includes(slug));
    const okF = !functions.length || functions.some((slug) => (item.f || []).includes(slug));
    if (!okI || !okF) return false;
    const needles = terms();
    if (!needles.length) return true;
    const hay = (item.h || `${item.t} ${item.u}`).toLowerCase();
    return needles.every((term) => hay.includes(term));
  };

  const parseList = (raw) =>
    String(raw || "")
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);

  const known = (slug, kind) => {
    if (!index) return true;
    if (kind === "i") return index.some((item) => (item.i || []).includes(slug));
    return index.some((item) => (item.f || []).includes(slug));
  };

  const readUrl = () => {
    const params = new URLSearchParams(location.search);
    const nextI = parseList(params.get("industry")).filter((slug) => slug && slug !== "all");
    const nextF = parseList(params.get("function") || params.get("functions"));
    industries = nextI;
    functions = nextF;
    if (q && params.has("q")) q.value = params.get("q") || "";
  };

  const writeUrl = (method) => {
    if (mode !== "hub") return;
    const params = new URLSearchParams();
    if (industries.length) params.set("industry", industries.join(","));
    if (functions.length) params.set("function", functions.join(","));
    const query = q ? q.value.trim() : "";
    if (query) params.set("q", query);
    const qs = params.toString();
    const next = qs ? `${location.pathname}?${qs}` : location.pathname;
    const current = `${location.pathname}${location.search}`;
    if (next === current) return;
    history[method]({}, "", next);
  };

  const syncTiles = () => {
    document.querySelectorAll(".uc-tile[data-industry]").forEach((tile) => {
      const on = industries.includes(tile.dataset.industry);
      tile.classList.toggle("is-active", on);
      tile.setAttribute("aria-current", on ? "true" : "false");
    });
    document.querySelectorAll("[data-function]").forEach((pill) => {
      const on = functions.includes(pill.dataset.function);
      pill.classList.toggle("is-active", on);
      if (pill.tagName === "BUTTON" || pill.getAttribute("role") === "button") {
        pill.setAttribute("aria-pressed", on ? "true" : "false");
      }
    });
    if (clearBtn) clearBtn.hidden = !filtering();
  };

  const ensureCards = (wanted) => {
    if (!index || !grid) return;
    const have = new Set([...grid.querySelectorAll("[data-slug]")].map((node) => node.getAttribute("data-slug")));
    let matchingInDom = 0;
    grid.querySelectorAll(".uc-card").forEach((card) => {
      const item = index.find((row) => row.s === card.dataset.slug);
      if (item && matches(item)) matchingInDom += 1;
    });
    const extras = [];
    for (const item of index) {
      if (have.has(item.s)) continue;
      if (!matches(item)) continue;
      if (matchingInDom + extras.length >= wanted) break;
      extras.push(item);
      have.add(item.s);
    }
    if (extras.length) grid.insertAdjacentHTML("beforeend", extras.map(cardHTML).join(""));
  };

  const apply = () => {
    const cards = grid ? [...grid.querySelectorAll(".uc-card")] : [...document.querySelectorAll(".uc-card")];
    const compactItems = [...document.querySelectorAll(".uc-compact")];
    const active = filtering();
    const wanted = active ? pageSize : mode === "hub" ? pageSize : pageSize;
    if (index) ensureCards(wanted);

    const visibleSlugs = [];
    const nodes = grid ? [...grid.querySelectorAll(".uc-card")] : cards;
    let shown = 0;
    nodes.forEach((card) => {
      const item = index
        ? index.find((row) => row.s === card.dataset.slug)
        : {
            s: card.dataset.slug,
            i: parseList(card.dataset.i),
            f: parseList(card.dataset.f),
            h: card.textContent,
          };
      const ok = item ? matches(item) : false;
      const featured = card.classList.contains("uc-featured");
      if (!ok) {
        card.hidden = true;
        return;
      }
      if (shown >= wanted && !(mode === "hub" && !active && featured && shown < 12)) {
        card.hidden = true;
        return;
      }
      card.hidden = false;
      shown += 1;
      visibleSlugs.push(card.dataset.slug);
    });

    compactItems.forEach((item) => {
      const row = {
        s: item.dataset.slug,
        i: parseList(item.dataset.i),
        f: parseList(item.dataset.f),
        h: item.textContent,
      };
      const ok = matches(row);
      item.hidden = !ok || (root.classList.contains("uc-js") && index);
    });

    const totalMatches = index ? index.filter(matches).length : shown;
    const total = index ? index.length : TOTAL || nodes.length;
    if (count) {
      count.textContent = "Showing " + shown + " of " + total + " use cases";
    }
    if (empty) empty.hidden = shown > 0;
    if (showMore) {
      const moreLeft = totalMatches > shown;
      showMore.hidden = !moreLeft;
      showMore.textContent = "Show more";
    }
    syncTiles();
  };

  const resetHub = () => {
    industries = [];
    functions = [];
    pageSize = 12;
    if (q) q.value = "";
    if (grid) grid.querySelectorAll(".uc-injected").forEach((node) => node.remove());
    writeUrl("pushState");
    apply();
  };

  const activateFilter = () => {
    pageSize = Math.max(pageSize, PAGE);
    loadIndex()
      .then(() => {
        industries = industries.filter((slug) => known(slug, "i"));
        functions = functions.filter((slug) => known(slug, "f"));
        apply();
      })
      .catch(() => apply());
  };

  if (mode === "hub") {
    readUrl();
    if (filtering()) {
      pageSize = PAGE;
      activateFilter();
    } else {
      apply();
    }

    document.querySelectorAll(".uc-tile[data-industry]").forEach((tile) => {
      tile.addEventListener("click", (event) => {
        if (!filtering() && !industries.length) return;
        event.preventDefault();
        const slug = tile.dataset.industry;
        if (industries.includes(slug)) industries = industries.filter((item) => item !== slug);
        else industries = [slug];
        pageSize = PAGE;
        writeUrl("pushState");
        activateFilter();
      });
    });

    document.querySelectorAll("[data-function]").forEach((pill) => {
      pill.addEventListener("click", (event) => {
        event.preventDefault();
        const slug = pill.dataset.function;
        if (functions.includes(slug)) functions = functions.filter((item) => item !== slug);
        else functions.push(slug);
        pageSize = PAGE;
        writeUrl("pushState");
        if (moreFilters && !moreFilters.open) moreFilters.open = true;
        activateFilter();
      });
    });

    if (q) {
      q.addEventListener("input", () => {
        writeUrl("replaceState");
        if (q.value.trim() || filtering()) activateFilter();
        else {
          pageSize = 12;
          if (grid) grid.querySelectorAll(".uc-injected").forEach((node) => node.remove());
          apply();
        }
      });
    }

    if (clearBtn) clearBtn.addEventListener("click", resetHub);

    window.addEventListener("popstate", () => {
      readUrl();
      pageSize = filtering() ? PAGE : 12;
      if (grid) grid.querySelectorAll(".uc-injected").forEach((node) => node.remove());
      if (filtering()) activateFilter();
      else apply();
    });
  } else if (lazy) {
    pageSize = 12;
    apply();
  }

  if (showMore) {
    showMore.addEventListener("click", () => {
      pageSize += PAGE;
      loadIndex()
        .then(apply)
        .catch(apply);
    });
  }
})();
