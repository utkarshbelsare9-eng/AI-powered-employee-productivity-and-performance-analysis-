// ==========================================================================
// AI-Powered Employee Productivity & Performance Analyzer — Core JS
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle (mobile)
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
  }

  // Auto-dismiss alerts
  document.querySelectorAll(".alert-dismissible").forEach((el) => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      if (alert) alert.close();
    }, 5000);
  });

  // Theme toggle
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const html = document.documentElement;
      const current = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", current);
      localStorage.setItem("preferredTheme", current);
      const icon = themeToggle.querySelector("i");
      if (icon) icon.className = current === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
    });
  }

  // Loading overlay on form submit for long-running actions (uploads, reports)
  document.querySelectorAll("form[data-loading]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
      }
    });
  });

  // Simple client-side table search filter
  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const targetTable = document.querySelector(input.dataset.tableSearch);
    if (!targetTable) return;
    input.addEventListener("keyup", () => {
      const term = input.value.toLowerCase();
      targetTable.querySelectorAll("tbody tr").forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  });

  // Range slider live label (task completion %)
  document.querySelectorAll('input[type="range"][data-live-label]').forEach((range) => {
    const label = document.querySelector(range.dataset.liveLabel);
    if (label) {
      const update = () => (label.textContent = range.value + "%");
      range.addEventListener("input", update);
      update();
    }
  });
});

// Chart.js default styling
if (window.Chart) {
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = "#7C7C93";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
}

const CHART_PALETTE = ["#6C5CE7", "#00CEC9", "#FD79A8", "#FDCB6E", "#4834d4", "#00B894", "#e17055"];
