(function () {
  "use strict";

  // Mobile sidebar toggle
  document.addEventListener("click", function (e) {
    var toggle = e.target.closest(".fl-menu-toggle");
    var shell = document.querySelector(".fl-shell");
    var sidebar = document.querySelector(".fl-sidebar");
    if (toggle && shell && sidebar) {
      sidebar.classList.toggle("open");
      shell.classList.toggle("nav-open");
      return;
    }
    if (shell && shell.classList.contains("nav-open") && !e.target.closest(".fl-sidebar")) {
      sidebar.classList.remove("open");
      shell.classList.remove("nav-open");
    }
  });

  // Auto-submit filter forms when a <select data-autosubmit> changes
  document.querySelectorAll("form [data-autosubmit]").forEach(function (el) {
    el.addEventListener("change", function () {
      el.form.requestSubmit ? el.form.requestSubmit() : el.form.submit();
    });
  });

  // Toggle the password field on the add-member form
  var needAccount = document.querySelector("[data-need-account]");
  if (needAccount) {
    var pwRow = document.querySelector("[data-password-row]");
    var sync = function () {
      var on = needAccount.value === "yes" || needAccount.checked;
      if (pwRow) pwRow.style.display = on ? "" : "none";
    };
    needAccount.addEventListener("change", sync);
    sync();
  }

  // Render Chart.js charts declared as <canvas data-chart='{...}'>
  function renderCharts() {
    if (typeof Chart === "undefined") return;
    var css = getComputedStyle(document.documentElement);
    var palette = {
      income: css.getPropertyValue("--fl-income").trim() || "#15a06a",
      expense: css.getPropertyValue("--fl-expense").trim() || "#e0413d",
      review: css.getPropertyValue("--fl-review").trim() || "#d98a10",
      brand: css.getPropertyValue("--fl-brand").trim() || "#4338ca",
      asset: css.getPropertyValue("--fl-asset").trim() || "#475569",
    };
    var categorical = ["#4338ca", "#15a06a", "#d98a10", "#e0413d", "#0ea5e9", "#8b5cf6", "#14b8a6", "#f97316", "#64748b", "#db2777"];

    document.querySelectorAll("canvas[data-chart]").forEach(function (canvas) {
      var cfg;
      try {
        cfg = JSON.parse(canvas.getAttribute("data-chart"));
      } catch (err) {
        return;
      }
      (cfg.data.datasets || []).forEach(function (ds, i) {
        if (ds._palette === "semantic") {
          ds.backgroundColor = [palette.income, palette.expense];
        } else if (ds._palette === "categorical") {
          ds.backgroundColor = categorical;
        } else if (ds._palette === "income") {
          ds.backgroundColor = palette.income;
          ds.borderColor = palette.income;
        } else if (ds._palette === "expense") {
          ds.backgroundColor = palette.expense;
          ds.borderColor = palette.expense;
        } else if (ds._palette === "brand") {
          ds.backgroundColor = palette.brand;
          ds.borderColor = palette.brand;
        }
      });
      cfg.options = cfg.options || {};
      cfg.options.responsive = true;
      cfg.options.maintainAspectRatio = false;
      new Chart(canvas.getContext("2d"), cfg);
    });
  }
  renderCharts();
})();
