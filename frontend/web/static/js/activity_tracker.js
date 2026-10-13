/**
 * Privacy-first browser activity tracker.
 * Collects aggregate counts only; never records key values or typed text.
 */
(function () {
  const PING_INTERVAL_MS = 60 * 1000;
  const PING_URL = "/api/activity/ping";
  const SUMMARY_URL = "/api/activity/summary";

  let mouseEvents = 0;
  let mouseClicks = 0;
  let mouseMoves = 0;
  let scrollEvents = 0;
  let keyboardEvents = 0;
  let lastInputAt = Date.now();

  function touch() { lastInputAt = Date.now(); }
  function onMouseMove() { mouseEvents++; mouseMoves++; touch(); }
  function onMouseDown() { mouseEvents++; mouseClicks++; touch(); }
  function onWheel() { mouseEvents++; scrollEvents++; touch(); }
  function onKeyboard() { keyboardEvents++; touch(); } // count only; do not inspect event.key

  function csrfToken() {
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute("content") : null;
  }

  function reset() {
    mouseEvents = mouseClicks = mouseMoves = scrollEvents = keyboardEvents = 0;
  }

  function updatePill(active) {
    const pill = document.getElementById("activityStatusPill");
    if (!pill) return;
    pill.classList.remove("activity-active", "activity-idle");
    pill.classList.add(active ? "activity-active" : "activity-idle");
    pill.innerHTML = active
      ? '<i class="fa-solid fa-circle"></i> Tracking activity'
      : '<i class="fa-regular fa-circle"></i> Idle';
  }

  function refreshSummary() {
    fetch(SUMMARY_URL, { credentials: "same-origin" })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const el = document.getElementById("activityHoursToday");
        if (el) el.textContent = Number(data.total_active_hours || 0).toFixed(2) + "h";
      }).catch(() => {});
  }

  function sendPing() {
    if (document.hidden) {
      reset();
      updatePill(false);
      return;
    }

    const now = Date.now();
    const idleSeconds = Math.max(0, Math.min(60, Math.floor((now - lastInputAt) / 1000)));
    const payload = {
      mouse_events: mouseEvents,
      mouse_clicks: mouseClicks,
      mouse_moves: mouseMoves,
      scroll_events: scrollEvents,
      keyboard_events: keyboardEvents,
      idle_seconds: idleSeconds,
      interval_seconds: 60,
      source: "browser"
    };

    updatePill(mouseEvents > 0 || keyboardEvents > 0);

    fetch(PING_URL, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken() ? { "X-CSRFToken": csrfToken() } : {})
      },
      body: JSON.stringify(payload)
    }).then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          const el = document.getElementById("activityHoursToday");
          if (el) el.textContent = Number(data.total_active_hours || 0).toFixed(2) + "h";
        }
      }).catch(() => {})
      .finally(reset);
  }

  function init() {
    document.addEventListener("mousemove", onMouseMove, { passive: true });
    document.addEventListener("mousedown", onMouseDown, { passive: true });
    document.addEventListener("wheel", onWheel, { passive: true });
    document.addEventListener("keydown", onKeyboard, { passive: true });

    refreshSummary();
    setInterval(sendPing, PING_INTERVAL_MS);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) updatePill(false);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
