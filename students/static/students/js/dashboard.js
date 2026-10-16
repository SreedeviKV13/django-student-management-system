// Optional department chart. Everything on the dashboard also works without it:
// the chart container stays hidden unless Chart.js loads and the chart is drawn.
(function () {
  "use strict";

  try {
    if (typeof Chart === "undefined") {
      return; // CDN blocked or offline: keep the progress bars only.
    }

    var dataElement = document.getElementById("chart-data");
    var canvas = document.getElementById("departmentChart");
    var wrapper = document.getElementById("chart-wrapper");
    if (!dataElement || !canvas || !wrapper) {
      return;
    }

    var data = JSON.parse(dataElement.textContent).departments;
    if (!data || !data.values.length) {
      return;
    }

    wrapper.classList.remove("d-none");

    var styles = getComputedStyle(document.documentElement);
    var navy = styles.getPropertyValue("--brand-navy").trim() || "#12284c";

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Students",
            data: data.values,
            backgroundColor: navy,
            borderRadius: 6,
            maxBarThickness: 48,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } },
          x: { grid: { display: false } },
        },
      },
    });
  } catch (error) {
    // Never let a chart problem break the page.
    var fallback = document.getElementById("chart-wrapper");
    if (fallback) {
      fallback.classList.add("d-none");
    }
    if (window.console) {
      console.warn("Dashboard chart could not be displayed:", error);
    }
  }
})();
