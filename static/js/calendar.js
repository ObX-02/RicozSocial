/* =========================================================
   RICOZ SOCIAL
   CONTENT CALENDAR
   Interactive Calendar
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const monthView = document.getElementById("monthView");
    const listView = document.getElementById("listView");

    const calendarGrid =
        document.getElementById("calendarGrid");

    const monthLabel =
        document.getElementById("calendarMonthLabel");

    const previousButton =
        document.getElementById("previousMonth");

    const nextButton =
        document.getElementById("nextMonth");

    const todayButton =
        document.getElementById("todayButton");

    const viewButtons =
        document.querySelectorAll(".view-switch");

    const calendarDataElement =
        document.getElementById("calendarData");

    const modal =
        document.getElementById("calendarEventModal");

    const closeModalButton =
        document.getElementById("closeCalendarModal");

    const closeModalBottom =
        document.getElementById("closeCalendarModalBottom");

    const modalBackdrop =
        modal?.querySelector(".calendar-modal-backdrop");


    if (!calendarGrid || !calendarDataElement) {
        console.warn(
            "RicozSocial Calendar: required elements missing."
        );
        return;
    }


    /* =====================================================
       DATA
    ===================================================== */

    let events = [];

    try {

        events = JSON.parse(
            calendarDataElement.textContent || "[]"
        );

        if (!Array.isArray(events)) {
            events = [];
        }

    } catch (error) {

        console.error(
            "RicozSocial Calendar: invalid calendar data.",
            error
        );

        events = [];

    }


    /* =====================================================
       DATE STATE
    ===================================================== */

    const now = new Date();

    let currentMonth =
        now.getMonth();

    let currentYear =
        now.getFullYear();


    /* =====================================================
       HELPERS
    ===================================================== */

    function parseDate(value) {

        if (!value) {
            return null;
        }

        const date =
            new Date(value);

        return Number.isNaN(
            date.getTime()
        )
            ? null
            : date;

    }


    function pad(value) {

        return String(value).padStart(2, "0");

    }


    function dateKey(date) {

        return [
            date.getFullYear(),
            pad(date.getMonth() + 1),
            pad(date.getDate())
        ].join("-");

    }


    function formatTime(date) {

        if (!date) {
            return "";
        }

        return date.toLocaleTimeString(
            undefined,
            {
                hour: "numeric",
                minute: "2-digit"
            }
        );

    }


    function formatMonth(year, month) {

        return new Date(
            year,
            month,
            1
        ).toLocaleDateString(
            undefined,
            {
                month: "long",
                year: "numeric"
            }
        );

    }


    function formatFullDate(date) {

        if (!date) {
            return "No date";
        }

        return date.toLocaleString(
            undefined,
            {
                weekday: "short",
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "numeric",
                minute: "2-digit"
            }
        );

    }


    function getEventDate(event) {

        const status =
            String(
                event.status || ""
            ).toLowerCase();


        if (
            status === "scheduled"
            && event.scheduled_at
        ) {

            return parseDate(
                event.scheduled_at
            );

        }


        if (
            status === "published"
            && event.published_at
        ) {

            return parseDate(
                event.published_at
            );

        }


        return parseDate(
            event.created_at
        );

    }


    /* =====================================================
       STATUS
    ===================================================== */

    function statusLabel(status) {

        const value =
            String(
                status || ""
            ).toLowerCase();


        if (value === "scheduled") {
            return "Scheduled";
        }

        if (value === "published") {
            return "Published";
        }

        if (value === "draft") {
            return "Draft";
        }

        return value
            ? value.charAt(0).toUpperCase()
              + value.slice(1)
            : "Unknown";

    }


    /* =====================================================
       RENDER CALENDAR
    ===================================================== */

    function renderCalendar() {

        calendarGrid.innerHTML = "";

        monthLabel.textContent =
            formatMonth(
                currentYear,
                currentMonth
            );


        const firstDay =
            new Date(
                currentYear,
                currentMonth,
                1
            );

        const lastDay =
            new Date(
                currentYear,
                currentMonth + 1,
                0
            );


        const firstWeekday =
            firstDay.getDay();

        const totalDays =
            lastDay.getDate();


        const previousMonthLastDay =
            new Date(
                currentYear,
                currentMonth,
                0
            ).getDate();


        const totalCells =
            Math.ceil(
                (firstWeekday + totalDays) / 7
            ) * 7;


        for (
            let index = 0;
            index < totalCells;
            index++
        ) {

            let dayNumber;
            let cellDate;
            let otherMonth = false;


            if (index < firstWeekday) {

                dayNumber =
                    previousMonthLastDay
                    - firstWeekday
                    + index
                    + 1;

                cellDate =
                    new Date(
                        currentYear,
                        currentMonth - 1,
                        dayNumber
                    );

                otherMonth = true;

            } else if (
                index >=
                firstWeekday + totalDays
            ) {

                dayNumber =
                    index
                    - firstWeekday
                    - totalDays
                    + 1;

                cellDate =
                    new Date(
                        currentYear,
                        currentMonth + 1,
                        dayNumber
                    );

                otherMonth = true;

            } else {

                dayNumber =
                    index
                    - firstWeekday
                    + 1;

                cellDate =
                    new Date(
                        currentYear,
                        currentMonth,
                        dayNumber
                    );

            }


            const cell =
                document.createElement("div");

            cell.className =
                "calendar-day";


            if (otherMonth) {
                cell.classList.add(
                    "other-month"
                );
            }


            if (
                cellDate.getFullYear()
                    === now.getFullYear()
                &&
                cellDate.getMonth()
                    === now.getMonth()
                &&
                cellDate.getDate()
                    === now.getDate()
            ) {

                cell.classList.add("today");

            }


            const number =
                document.createElement("div");

            number.className =
                "calendar-day-number";


            const numberSpan =
                document.createElement("span");

            numberSpan.textContent =
                dayNumber;


            number.appendChild(
                numberSpan
            );

            cell.appendChild(
                number
            );


            const key =
                dateKey(cellDate);


            const dayEvents =
                events.filter(event => {

                    const eventDate =
                        getEventDate(event);

                    return eventDate
                        && dateKey(eventDate)
                            === key;

                });


            dayEvents
                .slice(0, 4)
                .forEach(event => {

                    createEventButton(
                        event,
                        cell
                    );

                });


            if (dayEvents.length > 4) {

                const more =
                    document.createElement("div");

                more.className =
                    "calendar-event-brand";

                more.textContent =
                    `+${dayEvents.length - 4} more`;

                cell.appendChild(
                    more
                );

            }


            calendarGrid.appendChild(
                cell
            );

        }

    }


    /* =====================================================
       EVENT BUTTON
    ===================================================== */

    function createEventButton(
        event,
        container
    ) {

        const eventDate =
            getEventDate(event);

        const button =
            document.createElement("button");

        button.type = "button";

        button.className =
            "calendar-event";


        const status =
            String(
                event.status || ""
            ).toLowerCase();


        if (status) {

            button.classList.add(
                `status-${status}`
            );

        }


        const time =
            document.createElement("span");

        time.className =
            "calendar-event-time";

        time.textContent =
            formatTime(eventDate);


        const title =
            document.createElement("span");

        title.className =
            "calendar-event-title";

        title.textContent =
            event.title
            || "Untitled post";


        const brand =
            document.createElement("span");

        brand.className =
            "calendar-event-brand";

        brand.textContent =
            event.brand
            || "Ricoz";


        button.appendChild(time);
        button.appendChild(title);
        button.appendChild(brand);


        button.addEventListener(
            "click",
            () => {

                openEventModal(event);

            }
        );


        container.appendChild(
            button
        );

    }


    /* =====================================================
       MODAL
    ===================================================== */

    function openEventModal(event) {

        if (!modal) {
            return;
        }


        const status =
            String(
                event.status || ""
            ).toLowerCase();


        const eventDate =
            getEventDate(event);


        const avatar =
            document.getElementById(
                "modalEventAvatar"
            );

        const statusElement =
            document.getElementById(
                "modalEventStatus"
            );

        const title =
            document.getElementById(
                "modalEventTitle"
            );

        const brand =
            document.getElementById(
                "modalEventBrand"
            );

        const date =
            document.getElementById(
                "modalEventDate"
            );

        const platforms =
            document.getElementById(
                "modalEventPlatforms"
            );

        const content =
            document.getElementById(
                "modalEventContent"
            );


        if (avatar) {

            avatar.textContent =
                String(
                    event.brand
                    || "R"
                )
                    .trim()
                    .charAt(0)
                    .toUpperCase();

        }


        if (statusElement) {

            statusElement.className =
                "calendar-status";

            if (status) {

                statusElement.classList.add(
                    `status-${status}`
                );

            }

            statusElement.textContent =
                statusLabel(status);

        }


        if (title) {

            title.textContent =
                event.title
                || "Untitled post";

        }


        if (brand) {

            brand.textContent =
                event.brand
                || "Ricoz";

        }


        if (date) {

            date.textContent =
                formatFullDate(eventDate);

        }


        if (platforms) {

            platforms.textContent =
                event.platforms
                || "No platform selected";

        }


        if (content) {

            content.textContent =
                event.content
                || "No content available.";

        }


        modal.classList.add(
            "is-open"
        );

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.style.overflow =
            "hidden";

    }


    function closeEventModal() {

        if (!modal) {
            return;
        }

        modal.classList.remove(
            "is-open"
        );

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.style.overflow =
            "";

    }


    closeModalButton?.addEventListener(
        "click",
        closeEventModal
    );


    closeModalBottom?.addEventListener(
        "click",
        closeEventModal
    );


    modalBackdrop?.addEventListener(
        "click",
        closeEventModal
    );


    /* =====================================================
       LIST VIEW ACTIONS
    ===================================================== */

    document
        .querySelectorAll(".list-open-btn")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const id =
                        String(
                            button.dataset.eventId
                        );

                    const event =
                        events.find(
                            item =>
                                String(item.id)
                                === id
                        );

                    if (event) {
                        openEventModal(event);
                    }

                }
            );

        });


    /* =====================================================
       MONTH NAVIGATION
    ===================================================== */

    previousButton?.addEventListener(
        "click",
        () => {

            currentMonth--;

            if (currentMonth < 0) {

                currentMonth = 11;
                currentYear--;

            }

            renderCalendar();

        }
    );


    nextButton?.addEventListener(
        "click",
        () => {

            currentMonth++;

            if (currentMonth > 11) {

                currentMonth = 0;
                currentYear++;

            }

            renderCalendar();

        }
    );


    todayButton?.addEventListener(
        "click",
        () => {

            currentMonth =
                now.getMonth();

            currentYear =
                now.getFullYear();

            renderCalendar();

        }
    );


    /* =====================================================
       VIEW SWITCH
    ===================================================== */

    viewButtons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const view =
                    button.dataset.view;


                viewButtons.forEach(item => {

                    item.classList.toggle(
                        "active",
                        item === button
                    );

                });


                if (view === "list") {

                    monthView.hidden = true;
                    listView.hidden = false;

                } else {

                    monthView.hidden = false;
                    listView.hidden = true;

                }

            }
        );

    });


    /* =====================================================
       KEYBOARD
    ===================================================== */

    document.addEventListener(
        "keydown",
        event => {

            if (
                event.target.tagName === "INPUT"
                ||
                event.target.tagName === "SELECT"
                ||
                event.target.tagName === "TEXTAREA"
            ) {
                return;
            }


            if (
                event.key === "Escape"
                &&
                modal?.classList.contains("is-open")
            ) {

                closeEventModal();
                return;

            }


            if (event.key === "ArrowLeft") {

                previousButton?.click();

            }


            if (event.key === "ArrowRight") {

                nextButton?.click();

            }

        }
    );


    /* =====================================================
       INITIALIZE
    ===================================================== */

    renderCalendar();

});
