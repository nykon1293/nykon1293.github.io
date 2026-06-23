(() => {
  const script = document.currentScript;
  const configuredUrl = script?.dataset?.chatbotUrl || window.YONATAN_CHATBOT_URL || "";
  const chatbotUrl = configuredUrl.trim().replace(/\/$/, "");
  const isConfigured = chatbotUrl && !/your[-_]?chatbot|example\.com/i.test(chatbotUrl);

  const launcher = document.createElement("button");
  launcher.className = "portfolio-chatbot-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Open Yonatan's AI Project Scout");
  launcher.innerHTML = `
    <span class="portfolio-chatbot-launcher__spark">✦</span>
    <span class="portfolio-chatbot-launcher__text">Project Scout</span>
  `;

  const panel = document.createElement("section");
  panel.className = "portfolio-chatbot-panel";
  panel.setAttribute("aria-label", "Yonatan AI Project Scout");
  panel.setAttribute("aria-hidden", "true");
  panel.innerHTML = `
    <header class="portfolio-chatbot-panel__header">
      <div>
        <p class="portfolio-chatbot-panel__kicker">AI Project Scout</p>
        <h2>See if your project is a fit</h2>
      </div>
      <button class="portfolio-chatbot-panel__close" type="button" aria-label="Close chat">×</button>
    </header>
    <div class="portfolio-chatbot-panel__body">
      ${isConfigured
        ? `<iframe title="Yonatan AI Project Scout" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" src="${chatbotUrl}?embedded=1"></iframe>`
        : `<div class="portfolio-chatbot-panel__placeholder">
            <strong>AI assistant backend is ready but not connected yet.</strong>
            <p>The site has the launcher installed. After the backend is deployed, set <code>data-chatbot-url</code> on this script to enable the live assistant.</p>
            <a href="mailto:josh.gemmi@gmail.com">Email Yonatan instead</a>
          </div>`}
    </div>
  `;

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  const closeButton = panel.querySelector(".portfolio-chatbot-panel__close");
  function setOpen(open) {
    panel.classList.toggle("is-open", open);
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    launcher.setAttribute("aria-expanded", open ? "true" : "false");
  }

  launcher.addEventListener("click", () => setOpen(!panel.classList.contains("is-open")));
  closeButton?.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
})();
