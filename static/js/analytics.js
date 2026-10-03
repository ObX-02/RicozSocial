/* =========================================================
   RICOZSOCIAL
   INSIGHTS / ANALYTICS
   CHART ENGINE
========================================================= */

(function () {

    "use strict";


    /* =====================================================
       DATA
    ====================================================== */

    const data = window.RICOZ_ANALYTICS || {};

    const dates = data.dates || [];

    const impressions = data.impressions || [];

    const reach = data.reach || [];

    const engagement = data.engagement || [];

    const clicks = data.clicks || [];

    const platformLabels = data.platformLabels || [];

    const platformImpressions =
        data.platformImpressions || [];

    const platformReach =
        data.platformReach || [];

    const followerDates =
        data.followerDates || [];

    const followerValues =
        data.followerValues || [];


    /* =====================================================
       COLORS
    ====================================================== */

    const RED = "#c8171d";

    const RED_LIGHT = "rgba(200, 23, 29, 0.12)";

    const GREEN = "#1f9d55";

    const GRID = "#eeeeee";

    const TEXT = "#777777";


    /* =====================================================
       HELPERS
    ====================================================== */

    function getCanvas(id) {

        const canvas =
            document.getElementById(id);

        if (!canvas) {
            return null;
        }

        return canvas;

    }


    function formatNumber(value) {

        return new Intl.NumberFormat(
            "en-US"
        ).format(value || 0);

    }


    function drawEmptyChart(canvas, message) {

        if (!canvas) {
            return;
        }

        const ctx =
            canvas.getContext("2d");

        const rect =
            canvas.getBoundingClientRect();

        const width =
            rect.width || 500;

        const height =
            rect.height || 300;

        const ratio =
            window.devicePixelRatio || 1;

        canvas.width =
            width * ratio;

        canvas.height =
            height * ratio;

        ctx.scale(ratio, ratio);

        ctx.fillStyle = "#999999";

        ctx.font =
            "13px Arial";

        ctx.textAlign =
            "center";

        ctx.textBaseline =
            "middle";

        ctx.fillText(
            message,
            width / 2,
            height / 2
        );

    }


    /* =====================================================
       LINE CHART
    ====================================================== */

    function drawLineChart(
        canvas,
        labels,
        datasets
    ) {

        if (!canvas) {
            return;
        }

        if (!labels.length) {

            drawEmptyChart(
                canvas,
                "No analytics data available"
            );

            return;

        }

        const ctx =
            canvas.getContext("2d");

        const rect =
            canvas.getBoundingClientRect();

        const width =
            rect.width || 800;

        const height =
            rect.height || 320;

        const ratio =
            window.devicePixelRatio || 1;

        canvas.width =
            width * ratio;

        canvas.height =
            height * ratio;

        ctx.scale(ratio, ratio);

        ctx.clearRect(
            0,
            0,
            width,
            height
        );


        const padding = {
            top: 24,
            right: 22,
            bottom: 42,
            left: 55
        };


        const chartWidth =
            width -
            padding.left -
            padding.right;

        const chartHeight =
            height -
            padding.top -
            padding.bottom;


        let maxValue = 0;

        datasets.forEach(function (dataset) {

            dataset.values.forEach(function (value) {

                if (value > maxValue) {
                    maxValue = value;
                }

            });

        });


        if (maxValue === 0) {
            maxValue = 10;
        }


        maxValue =
            maxValue * 1.12;


        /* -------------------------------------------------
           GRID
        -------------------------------------------------- */

        ctx.strokeStyle =
            GRID;

        ctx.lineWidth = 1;

        ctx.fillStyle =
            TEXT;

        ctx.font =
            "10px Arial";

        ctx.textAlign =
            "right";

        ctx.textBaseline =
            "middle";


        const gridLines = 5;


        for (
            let i = 0;
            i <= gridLines;
            i++
        ) {

            const y =
                padding.top +
                (
                    chartHeight /
                    gridLines
                ) * i;

            ctx.beginPath();

            ctx.moveTo(
                padding.left,
                y
            );

            ctx.lineTo(
                width -
                padding.right,
                y
            );

            ctx.stroke();


            const value =
                maxValue -
                (
                    maxValue /
                    gridLines
                ) * i;

            ctx.fillText(
                formatNumber(
                    Math.round(value)
                ),
                padding.left - 8,
                y
            );

        }


        /* -------------------------------------------------
           X AXIS LABELS
        -------------------------------------------------- */

        ctx.textAlign =
            "center";

        ctx.textBaseline =
            "top";

        const labelStep =
            Math.max(
                1,
                Math.ceil(
                    labels.length / 7
                )
            );


        labels.forEach(function (
            label,
            index
        ) {

            if (
                index % labelStep !== 0 &&
                index !== labels.length - 1
            ) {
                return;
            }

            const x =
                padding.left +
                (
                    index /
                    Math.max(
                        labels.length - 1,
                        1
                    )
                ) *
                chartWidth;


            ctx.fillStyle =
                TEXT;

            ctx.fillText(
                label,
                x,
                height -
                padding.bottom +
                12
            );

        });


        /* -------------------------------------------------
           DATA LINES
        -------------------------------------------------- */

        datasets.forEach(function (
            dataset
        ) {

            const values =
                dataset.values || [];

            if (!values.length) {
                return;
            }


            ctx.beginPath();


            values.forEach(function (
                value,
                index
            ) {

                const x =
                    padding.left +
                    (
                        index /
                        Math.max(
                            values.length - 1,
                            1
                        )
                    ) *
                    chartWidth;


                const y =
                    padding.top +
                    chartHeight -
                    (
                        value /
                        maxValue
                    ) *
                    chartHeight;


                if (index === 0) {

                    ctx.moveTo(
                        x,
                        y
                    );

                } else {

                    ctx.lineTo(
                        x,
                        y
                    );

                }

            });


            ctx.strokeStyle =
                dataset.color;

            ctx.lineWidth = 2;

            ctx.stroke();


            /* ---------------------------------------------
               POINTS
            ---------------------------------------------- */

            values.forEach(function (
                value,
                index
            ) {

                const x =
                    padding.left +
                    (
                        index /
                        Math.max(
                            values.length - 1,
                            1
                        )
                    ) *
                    chartWidth;


                const y =
                    padding.top +
                    chartHeight -
                    (
                        value /
                        maxValue
                    ) *
                    chartHeight;


                ctx.beginPath();

                ctx.arc(
                    x,
                    y,
                    2.5,
                    0,
                    Math.PI * 2
                );

                ctx.fillStyle =
                    dataset.color;

                ctx.fill();

            });

        });


        /* -------------------------------------------------
           LEGEND
        -------------------------------------------------- */

        let legendX =
            padding.left;

        const legendY = 8;


        datasets.forEach(function (
            dataset
        ) {

            ctx.fillStyle =
                dataset.color;

            ctx.fillRect(
                legendX,
                legendY,
                18,
                3
            );


            ctx.fillStyle =
                "#555555";

            ctx.font =
                "10px Arial";

            ctx.textAlign =
                "left";

            ctx.textBaseline =
                "middle";

            ctx.fillText(
                dataset.label,
                legendX + 25,
                legendY + 2
            );


            legendX +=
                ctx.measureText(
                    dataset.label
                ).width + 70;

        });

    }


    /* =====================================================
       BAR CHART
    ====================================================== */

    function drawBarChart(
        canvas,
        labels,
        values
    ) {

        if (!canvas) {
            return;
        }

        if (!labels.length) {

            drawEmptyChart(
                canvas,
                "No platform data available"
            );

            return;

        }


        const ctx =
            canvas.getContext("2d");

        const rect =
            canvas.getBoundingClientRect();

        const width =
            rect.width || 500;

        const height =
            rect.height || 270;

        const ratio =
            window.devicePixelRatio || 1;

        canvas.width =
            width * ratio;

        canvas.height =
            height * ratio;

        ctx.scale(ratio, ratio);


        const padding = {
            top: 20,
            right: 20,
            bottom: 55,
            left: 52
        };


        const chartWidth =
            width -
            padding.left -
            padding.right;

        const chartHeight =
            height -
            padding.top -
            padding.bottom;


        let maxValue =
            Math.max(
                ...values,
                0
            );


        if (maxValue === 0) {
            maxValue = 10;
        }


        maxValue *= 1.12;


        /* -------------------------------------------------
           GRID
        -------------------------------------------------- */

        ctx.strokeStyle =
            GRID;

        ctx.lineWidth = 1;

        ctx.fillStyle =
            TEXT;

        ctx.font =
            "10px Arial";

        ctx.textAlign =
            "right";

        ctx.textBaseline =
            "middle";


        for (
            let i = 0;
            i <= 4;
            i++
        ) {

            const y =
                padding.top +
                (
                    chartHeight /
                    4
                ) * i;


            ctx.beginPath();

            ctx.moveTo(
                padding.left,
                y
            );

            ctx.lineTo(
                width -
                padding.right,
                y
            );

            ctx.stroke();


            const value =
                maxValue -
                (
                    maxValue /
                    4
                ) * i;


            ctx.fillText(
                formatNumber(
                    Math.round(value)
                ),
                padding.left - 8,
                y
            );

        }


        /* -------------------------------------------------
           BARS
        -------------------------------------------------- */

        const count =
            labels.length;

        const gap = 16;

        const barWidth =
            Math.max(
                18,
                (
                    chartWidth -
                    (
                        gap *
                        (count - 1)
                    )
                ) / count
            );


        labels.forEach(function (
            label,
            index
        ) {

            const value =
                values[index] || 0;


            const barHeight =
                (
                    value /
                    maxValue
                ) *
                chartHeight;


            const x =
                padding.left +
                index *
                (
                    barWidth +
                    gap
                );


            const y =
                padding.top +
                chartHeight -
                barHeight;


            ctx.fillStyle =
                RED;

            ctx.fillRect(
                x,
                y,
                barWidth,
                barHeight
            );


            /* value */

            ctx.fillStyle =
                "#555555";

            ctx.font =
                "9px Arial";

            ctx.textAlign =
                "center";

            ctx.textBaseline =
                "bottom";

            ctx.fillText(
                formatNumber(value),
                x +
                barWidth / 2,
                y - 5
            );


            /* label */

            ctx.fillStyle =
                TEXT;

            ctx.font =
                "10px Arial";

            ctx.textAlign =
                "center";

            ctx.textBaseline =
                "top";


            ctx.save();

            ctx.translate(
                x +
                barWidth / 2,
                height -
                padding.bottom +
                10
            );

            if (label.length > 9) {

                ctx.rotate(
                    -Math.PI / 7
                );

            }

            ctx.fillText(
                label,
                0,
                0
            );

            ctx.restore();

        });

    }


    /* =====================================================
       PERFORMANCE CHART
    ====================================================== */

    const performanceCanvas =
        getCanvas(
            "performanceChart"
        );


    drawLineChart(
        performanceCanvas,
        dates,
        [
            {
                label: "Impressions",
                values: impressions,
                color: RED
            },
            {
                label: "Reach",
                values: reach,
                color: "#777777"
            },
            {
                label: "Engagement",
                values: engagement,
                color: GREEN
            },
            {
                label: "Clicks",
                values: clicks,
                color: "#333333"
            }
        ]
    );


    /* =====================================================
       PLATFORM CHART
    ====================================================== */

    const platformCanvas =
        getCanvas(
            "platformChart"
        );


    drawBarChart(
        platformCanvas,
        platformLabels,
        platformReach
    );


    /* =====================================================
       FOLLOWER CHART
    ====================================================== */

    const followerCanvas =
        getCanvas(
            "followerChart"
        );


    drawLineChart(
        followerCanvas,
        followerDates,
        [
            {
                label: "Followers",
                values: followerValues,
                color: RED
            }
        ]
    );


    /* =====================================================
       RESIZE
    ====================================================== */

    let resizeTimer = null;


    window.addEventListener(
        "resize",
        function () {

            clearTimeout(
                resizeTimer
            );


            resizeTimer =
                setTimeout(
                    function () {

                        drawLineChart(
                            performanceCanvas,
                            dates,
                            [
                                {
                                    label: "Impressions",
                                    values: impressions,
                                    color: RED
                                },
                                {
                                    label: "Reach",
                                    values: reach,
                                    color: "#777777"
                                },
                                {
                                    label: "Engagement",
                                    values: engagement,
                                    color: GREEN
                                },
                                {
                                    label: "Clicks",
                                    values: clicks,
                                    color: "#333333"
                                }
                            ]
                        );


                        drawBarChart(
                            platformCanvas,
                            platformLabels,
                            platformReach
                        );


                        drawLineChart(
                            followerCanvas,
                            followerDates,
                            [
                                {
                                    label: "Followers",
                                    values: followerValues,
                                    color: RED
                                }
                            ]
                        );

                    },
                    150
                );

        }
    );

})();