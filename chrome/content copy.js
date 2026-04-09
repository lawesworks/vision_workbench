(() => {
  const CONFIG = {
    overlayId: "armada-yolo-overlay-root",
    appBase: "http://127.0.0.1:8000",
    autoShowOnMatch: true,
    defaultRoute: "/",
    sidebarFallbackWidth: 170,
    matchPrefix: "https://console.armada.ai/my-apps",
    routes: [
      { label: "Home", path: "/" },
      { label: "Settings", path: "/page-config" },
      { label: "Image", path: "/inference-uploaded" },
      { label: "Webcam", path: "/stream/webcam?index=0" },
      { label: "RTSP", path: "/stream/rtsp?url=rtsp://192.168.1.160:8554/live" }
    ]
  };

  
  let overlayEnabled = false;
  //let closeBtn = null;
  let overlayEl = null;
  let iframeEl = null;
  let statusEl = null;
  let loadingEl = null;
  let mutationObserver = null;
  let lastUrl = location.href;

  function isMatchingPage(url = location.href) {
    return url.startsWith(CONFIG.matchPrefix);
  }

  function fullUrl(path) {
    if (/^https?:\/\//i.test(path)) return path;
    return `${CONFIG.appBase.replace(/\/$/, "")}${path}`;
  }

  function getLeftSidebarWidth() {
    const candidates = [...document.querySelectorAll("body *")]
      .map((el) => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        return { el, rect, style };
      })
      .filter(({ rect, style }) => {
        return (
          rect.left >= -2 &&
          rect.top >= 0 &&
          rect.width >= 120 &&
          rect.width <= 320 &&
          rect.height >= window.innerHeight * 0.55 &&
          style.display !== "none" &&
          style.visibility !== "hidden"
        );
      });

    const navHints = ["Fleet Map", "Assets & Groups", "Connectivity", "Support", "Settings"];

    for (const { el, rect } of candidates) {
      const text = (el.innerText || "").trim();
      const matches = navHints.filter((t) => text.includes(t)).length;
      if (matches >= 2) return Math.round(rect.right);
    }

    if (candidates.length) {
      candidates.sort((a, b) => b.rect.height - a.rect.height);
      return Math.round(candidates[0].rect.right);
    }

    return CONFIG.sidebarFallbackWidth;
  }

  /*
  function syncOverlayBounds() {
    if (!overlayEl) return;

    const left = getLeftSidebarWidth();
    overlayEl.style.left = `${left}px`;
    overlayEl.style.width = `calc(100vw - ${left}px)`;
  }
    */

  function syncOverlayBounds() {
    if (!overlayEl) return;

    const left = getLeftSidebarWidth();
    overlayEl.style.left = `${left}px`;
    overlayEl.style.right = "0";
    overlayEl.style.width = "auto";
  }

  function highlightActive(path) {
    if (!overlayEl) return;

    const buttons = overlayEl.querySelectorAll("[data-route-path]");
    buttons.forEach((btn) => {
      const active = btn.getAttribute("data-route-path") === path;
      btn.classList.toggle("ayo-btn-active", active);
    });
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  /*
  function loadRoute(path) {
    if (!iframeEl) return;
    setStatus(`Loading ${path} ...`);
    iframeEl.src = fullUrl(path);
    highlightActive(path);
  }
  */

  /*
  async function loadRoute(path) {
    if (!iframeEl) return;

    const currentSrc = iframeEl.getAttribute("src") || "";
    const currentIsWebcam = currentSrc.includes("/stream/webcam");
    const nextIsWebcam = isWebcamRoute(path);

    // If leaving the webcam route, explicitly stop webcam 0
    if (currentIsWebcam && !nextIsWebcam) {
      setStatus("Stopping webcam...");
      await stopBackendWebcam(0);
    }

    setStatus(`Loading ${path} ...`);
    iframeEl.src = fullUrl(path);
    highlightActive(path);
  }
    */

  async function loadRoute(path) {
    if (!iframeEl) return;

    const currentSrc = iframeEl.getAttribute("src") || "";
    const currentIsWebcam = currentSrc.includes("/stream/webcam");
    const nextIsWebcam = isWebcamRoute(path);
    const nextIsRtsp = typeof path === "string" && path.startsWith("/stream/rtsp");
    const nextIsStream = nextIsWebcam || nextIsRtsp;

    if (currentIsWebcam && !nextIsWebcam) {
      await stopBackendWebcam(0);
    }

    if (nextIsRtsp) {
      showLoader("Connecting to RTSP stream...");
    } else if (nextIsWebcam) {
      showLoader("Starting webcam...");
    } else {
      showLoader("Loading...");
    }

    iframeEl.src = fullUrl(path);
    highlightActive(path);

    // For stream endpoints, iframe load is unreliable.
    // Hide the loader after a short delay so the stream can become visible.
    if (nextIsStream) {
      window.setTimeout(() => {
        hideLoader();
      }, 1200);
    }
  }


  // Webcam Helper Function (STOP)
  async function stopBackendWebcam(index = 0) {
    try {
      const response = await fetch(fullUrl(`/stop-webcam?index=${index}`), {
        method: "POST"
      });

      const data = await response.json();
      console.log("stop-webcam:", data);
      return data;
    } catch (err) {
      console.error("Failed to stop webcam:", err);
      return null;
    }
  }

  // Webcam Helper Function (Route)
  function isWebcamRoute(path) {
    return typeof path === "string" && path.startsWith("/stream/webcam");
  }

  /*
  const stopBtn = document.createElement("button");
  stopBtn.textContent = "Stop Webcam";
  stopBtn.style.marginTop = "10px";

  stopBtn.onclick = async () => {
      // 1. stop displaying stream
      if (imgElem) {
          imgElem.src = "";
          imgElem.removeAttribute("src");
      }

      // 2. tell backend to release webcam
      try {
          const res = await fetch("http://127.0.0.1:8000/stop-webcam?index=0", {
              method: "POST"
          });

          const data = await res.json();
          console.log("stop-webcam:", data);
      } catch (err) {
          console.error("Failed to stop webcam:", err);
      }
  };
  */

  function buildButton(label, className = "") {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `ayo-btn ${className}`.trim();
    btn.textContent = label;
    return btn;
  }

  
  // Loader Helper Functions (SHOW)
  function showLoader(message = "Loading...") {
    if (loadingEl) {
      const textEl = loadingEl.querySelector(".ayo-loading-text");
      if (textEl) textEl.textContent = message;
      loadingEl.style.display = "flex";
    }

    if (iframeEl) {
      iframeEl.style.visibility = "hidden";
    }

    setStatus("");
  }

  // Loader Helper Functions (HIDE)
  function hideLoader() {
    if (loadingEl) {
      loadingEl.style.display = "none";
    }

    if (iframeEl) {
      iframeEl.style.visibility = "visible";
    }

    setStatus("");
  }




  function createOverlay() {
    const existing = document.getElementById(CONFIG.overlayId);
    if (existing) {
      overlayEl = existing;
      iframeEl = overlayEl.querySelector("iframe");
      statusEl = overlayEl.querySelector(".ayo-status");
      loadingEl = overlayEl.querySelector(".ayo-loading");
      overlayEnabled = true;
      syncOverlayBounds();
      return;
    }

    overlayEl = document.createElement("div");
    overlayEl.id = CONFIG.overlayId;
    overlayEl.className = "ayo-overlay";

    const toolbar = document.createElement("div");
    toolbar.className = "ayo-toolbar";

    const leftGroup = document.createElement("div");
    leftGroup.className = "ayo-toolbar-group ayo-toolbar-left";

    const title = document.createElement("div");
    title.className = "ayo-title";
    title.textContent = "Vision AI";
    leftGroup.appendChild(title);

    CONFIG.routes.forEach((route) => {
      const btn = buildButton(route.label);
      btn.setAttribute("data-route-path", route.path);
      btn.addEventListener("click", () => loadRoute(route.path));
      leftGroup.appendChild(btn);
    });

    const rightGroup = document.createElement("div");
    rightGroup.className = "ayo-toolbar-group ayo-toolbar-right";

    const openBtn = buildButton("Open in Tab", "ayo-btn-secondary");
    openBtn.addEventListener("click", () => {
      if (iframeEl?.src) {
        window.open(iframeEl.src, "_blank", "noopener,noreferrer");
      }
    });

    const reloadBtn = buildButton("Reload", "ayo-btn-secondary");
    reloadBtn.addEventListener("click", () => {
      if (!iframeEl) return;
      setStatus("Reloading...");
      iframeEl.src = iframeEl.src;
    });

    const closeBtn = buildButton("Close", "ayo-btn-danger");
    closeBtn.addEventListener("click", async () => {
      try {
        if (iframeEl?.src && iframeEl.src.includes("/stream/webcam")) {
          await stopBackendWebcam(0);
        }

        hideOverlay();
        await chrome.storage.local.set({ armadaYoloOverlayEnabled: false });
      } catch (err) {
        console.warn("Storage error while disabling overlay:", err);
      }
    });

    rightGroup.appendChild(openBtn);
    rightGroup.appendChild(reloadBtn);
    rightGroup.appendChild(closeBtn);

    toolbar.appendChild(leftGroup);
    toolbar.appendChild(rightGroup);

    const main = document.createElement("div");
    main.className = "ayo-main";

    statusEl = document.createElement("div");
    statusEl.className = "ayo-status";
    statusEl.textContent = "Loading app...";

    loadingEl = document.createElement("div");
    loadingEl.className = "ayo-loading";
    loadingEl.innerHTML = `
      <div class="ayo-spinner"></div>
      <div class="ayo-loading-text">Loading...</div>
    `;

    iframeEl = document.createElement("iframe");
    iframeEl.className = "ayo-iframe";
    iframeEl.src = fullUrl(CONFIG.defaultRoute);
    iframeEl.allow = "camera; microphone; fullscreen";

    /*
    iframeEl.addEventListener("load", () => {
      setStatus("");
    });
    */
   iframeEl.addEventListener("load", () => {
      hideLoader();
   });
    main.appendChild(statusEl);
    main.appendChild(loadingEl); 
    main.appendChild(iframeEl);

    overlayEl.appendChild(toolbar);
    overlayEl.appendChild(main);

    document.body.appendChild(overlayEl);

    mutationObserver = new MutationObserver(() => {
      syncOverlayBounds();
    });

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true
    });

    window.addEventListener("resize", syncOverlayBounds);
    syncOverlayBounds();
    highlightActive(CONFIG.defaultRoute);
    overlayEnabled = true;
  }

  function showOverlay() {
    if (!isMatchingPage()) return;

    createOverlay();
    overlayEl.style.display = "flex";
    overlayEnabled = true;
    syncOverlayBounds();
  }

  function hideOverlay() {
    if (overlayEl) {
      overlayEl.style.display = "none";
    }
    overlayEnabled = false;
  }

  function destroyOverlay() {
    if (mutationObserver) {
      mutationObserver.disconnect();
      mutationObserver = null;
    }

    window.removeEventListener("resize", syncOverlayBounds);

    if (overlayEl) {
      overlayEl.remove();
      overlayEl = null;
      iframeEl = null;
      statusEl = null;
      loadingEl = null;
    }

    overlayEnabled = false;
  }

  async function toggleOverlay() {
    if (!isMatchingPage()) return;

    try {
      if (!overlayEl || overlayEl.style.display === "none") {
        showOverlay();
        await chrome.storage.local.set({ armadaYoloOverlayEnabled: true });
      } else {
        hideOverlay();
        await chrome.storage.local.set({ armadaYoloOverlayEnabled: false });
      }
    } catch (err) {
      console.warn("Storage error while toggling overlay:", err);
    }
  }

  async function checkAndShowOverlay() {
    if (!isMatchingPage()) return;

    try {
      const result = await chrome.storage.local.get(["armadaYoloOverlayEnabled"]);
      const enabled = result.armadaYoloOverlayEnabled;

      if (enabled || (enabled === undefined && CONFIG.autoShowOnMatch)) {
        showOverlay();
      }
    } catch (err) {
      console.warn("Storage error while checking overlay state:", err);
    }
  }

  async function handleUrlChange() {
    if (location.href === lastUrl) return;
    lastUrl = location.href;

    if (isMatchingPage()) {
      await checkAndShowOverlay();
    } else {
      destroyOverlay();
    }
  }

  function watchSpaNavigation() {
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function (...args) {
      const ret = originalPushState.apply(this, args);
      queueMicrotask(() => {
        handleUrlChange();
      });
      return ret;
    };

    history.replaceState = function (...args) {
      const ret = originalReplaceState.apply(this, args);
      queueMicrotask(() => {
        handleUrlChange();
      });
      return ret;
    };

    window.addEventListener("popstate", () => {
      handleUrlChange();
    });

    setInterval(() => {
      handleUrlChange();
    }, 800);
  }

  chrome.runtime.onMessage.addListener((message) => {
    if (!message || typeof message !== "object") return;

    if (message.type === "TOGGLE_OVERLAY") {
      toggleOverlay();
    }
  });

  checkAndShowOverlay();
  watchSpaNavigation();
})();