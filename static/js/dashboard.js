cat > static/js/dashboard.js <<'EOF'
/* =========================================================
   RICOZSOCIAL
   DASHBOARD JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const canvas =
        document.getElementById("dashboardAnalyticsChart");

    if (!canvas) {
        return;
    }

    const analytics =
        Array.isArray(window.dashboardAnalytics)
            ? window.dashboardAnalytics
            : [];


    /* =====================================================
       EMPTY DATA
    ===================================================== */

    if (
        typeof Chart === "undefined"
        || analytics.length === 0
    ) {
        return;
    }


    /* =====================================================
       DATA
    ===================================================== */

    const labels = analytics.map(item => {

        return (
            item.metric_date
            || item.date
            || ""
        );

    });


    const impressions = analytics.map(item => {

        return Number(
            item.impressions || 0
        );

    });


    const reach = analytics.map(item => {

        return Number(
            item.reach || 0
        );

    });


    /* =====================================================
       CHART
    ===================================================== */

    new Chart(canvas, {

        type: "line",

        data: {

            labels: labels,

            datasets: [

                {
                    label: "Impressions",

                    data: impressions,

                    borderColor: "#dc2626",

                    backgroundColor:
                        "rgba(220, 38, 38, 0.08)",

                    borderWidth: 2.5,

                    pointRadius: 3,

                    pointHoverRadius: 5,

                    pointBackgroundColor: "#ffffff",

                    pointBorderColor: "#dc2626",

                    pointBorderWidth: 2,

                    fill: true,

                    tension: 0.4
                },

                {
                    label: "Reach",

                    data: reach,

                    borderColor: "#27272a",

                    backgroundColor:
                        "rgba(39, 39, 42, 0.03)",

                    borderWidth: 2,

                    pointRadius: 2,

                    pointHoverRadius: 4,

                    pointBackgroundColor: "#ffffff",

                    pointBorderColor: "#27272a",

                    pointBorderWidth: 2,

                    fill: true,

                    tension: 0.4
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {

                legend: {

                    position: "top",

                    align: "end",

                    labels: {

                        usePointStyle: true,

                        pointStyle: "circle",

                        boxWidth: 7,

                        boxHeight: 7,

                        padding: 14,

                        color: "#777",

                        font: {
                            size: 10,
                            weight: "600"
                        }

                    }

                },

                tooltip: {

                    backgroundColor: "#18181b",

                    titleColor: "#ffffff",

                    bodyColor: "#e4e4e7",

                    borderColor: "#dc2626",

                    borderWidth: 1,

                    padding: 10,

                    displayColors: true,

                    cornerRadius: 9

                }

            },

            scales: {

                x: {

                    grid: {
                        display: false
                    },

                    border: {
                        display: false
                    },

                    ticks: {

                        color: "#a1a1aa",

                        font: {
                            size: 9
                        },

                        maxRotation: 0

                    }

                },

                y: {

                    beginAtZero: true,

                    grid: {

                        color:
                            "rgba(0, 0, 0, 0.055)"

                    },

                    border: {
                        display: false
                    },

                    ticks: {

                        color: "#a1a1aa",

                        font: {
                            size: 9
                        },

                        padding: 7

                    }

                }

            }

        }

    });

});
EOF