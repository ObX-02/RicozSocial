/* =========================================================
   RICOZSOCIAL
   CONTENT APPROVALS JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {


    /* =====================================================
       APPROVE CONFIRMATION
    ===================================================== */

    document.addEventListener("submit", (event) => {

        const form =
            event.target.closest(
                "form[data-approval-action='approve']"
            );

        if (!form) {
            return;
        }

        const confirmed = window.confirm(
            "Are you sure you want to approve this content?"
        );

        if (!confirmed) {

            event.preventDefault();

            return;

        }

        const button =
            form.querySelector(
                "button[type='submit']"
            );

        if (button) {

            button.disabled = true;

            button.textContent =
                "Approving...";

        }

    });


    /* =====================================================
       REJECT CONFIRMATION
    ===================================================== */

    document.addEventListener("submit", (event) => {

        const form =
            event.target.closest(
                "form[data-approval-action='reject']"
            );

        if (!form) {
            return;
        }

        const textarea =
            form.querySelector(
                "textarea[name='comments']"
            );

        if (textarea && !textarea.value.trim()) {

            event.preventDefault();

            showApprovalMessage(
                "Please provide a rejection comment.",
                "error"
            );

            textarea.focus();

            return;

        }

        const confirmed = window.confirm(
            "Are you sure you want to reject this content?"
        );

        if (!confirmed) {

            event.preventDefault();

            return;

        }

        const button =
            form.querySelector(
                "button[type='submit']"
            );

        if (button) {

            button.disabled = true;

            button.textContent =
                "Rejecting...";

        }

    });


    /* =====================================================
       AUTO RESIZE COMMENT BOX
    ===================================================== */

    document.querySelectorAll(
        ".approval-comment-box"
    ).forEach((textarea) => {

        textarea.addEventListener(
            "input",
            () => {

                textarea.style.height = "auto";

                textarea.style.height =
                    `${textarea.scrollHeight}px`;

            }
        );

    });


    /* =====================================================
       SEARCH FORM
    ===================================================== */

    const searchInput =
        document.querySelector(
            ".approvals-filter-form input[name='search']"
        );

    if (searchInput) {

        searchInput.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    const form =
                        searchInput.closest("form");

                    if (form) {
                        form.submit();
                    }

                }

            }
        );

    }


    /* =====================================================
       STATUS FILTER
    ===================================================== */

    const statusSelect =
        document.querySelector(
            ".approvals-filter-form select[name='status']"
        );

    if (statusSelect) {

        statusSelect.addEventListener(
            "change",
            () => {

                const form =
                    statusSelect.closest("form");

                if (form) {
                    form.submit();
                }

            }
        );

    }


    /* =====================================================
       BRAND FILTER
    ===================================================== */

    const brandSelect =
        document.querySelector(
            ".approvals-filter-form select[name='brand_id']"
        );

    if (brandSelect) {

        brandSelect.addEventListener(
            "change",
            () => {

                const form =
                    brandSelect.closest("form");

                if (form) {
                    form.submit();
                }

            }
        );

    }


    /* =====================================================
       MESSAGE HELPER
    ===================================================== */

    function showApprovalMessage(
        message,
        type = "error"
    ) {

        const existing =
            document.querySelector(
                ".approval-js-message"
            );

        if (existing) {
            existing.remove();
        }

        const box =
            document.createElement("div");

        box.className =
            "approval-js-message";

        box.textContent = message;

        const isError =
            type === "error";

        box.style.position = "fixed";
        box.style.top = "24px";
        box.style.right = "24px";
        box.style.zIndex = "10000";

        box.style.padding =
            "13px 17px";

        box.style.borderRadius =
            "10px";

        box.style.fontSize =
            "13px";

        box.style.fontWeight =
            "700";

        box.style.background =
            isError
                ? "#fff1f1"
                : "#eaf7ef";

        box.style.color =
            isError
                ? "#c62828"
                : "#198754";

        box.style.border =
            isError
                ? "1px solid #f2b8b8"
                : "1px solid #b8dfc6";

        box.style.boxShadow =
            "0 10px 30px rgba(0,0,0,.10)";

        document.body.appendChild(box);


        setTimeout(() => {

            box.style.opacity = "0";

            box.style.transition =
                "opacity .25s ease";

            setTimeout(() => {

                box.remove();

            }, 250);

        }, 3000);

    }


    /* =====================================================
       ROW HIGHLIGHT AFTER ACTION
    ===================================================== */

    document.querySelectorAll(
        ".approvals-table tbody tr"
    ).forEach((row) => {

        row.addEventListener(
            "mouseenter",
            () => {

                row.dataset.hovered = "true";

            }
        );

    });

});