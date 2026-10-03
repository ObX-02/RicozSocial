/* =========================================================
   RICOZSOCIAL
   PUBLISHER JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTS
    ===================================================== */

    const createModal = document.getElementById("createPostModal");
    const detailsModal = document.getElementById("postDetailsModal");

    const openCreateBtn = document.getElementById("openCreatePost");
    const closeCreateBtn = document.getElementById("closeCreatePost");

    const closeDetailsBtn = document.getElementById("closePostDetails");

    const brandSelect = document.getElementById("publisherBrand");
    const statusSelect = document.getElementById("publisherStatus");
    const scheduleField = document.getElementById("scheduleField");

    const detailsContent = document.getElementById("postDetailsContent");


    /* =====================================================
       MODAL HELPERS
    ===================================================== */

    function openModal(modal) {

        if (!modal) {
            return;
        }

        modal.classList.add("active");
        document.body.style.overflow = "hidden";
    }


    function closeModal(modal) {

        if (!modal) {
            return;
        }

        modal.classList.remove("active");

        if (
            !createModal?.classList.contains("active") &&
            !detailsModal?.classList.contains("active")
        ) {
            document.body.style.overflow = "";
        }
    }


    /* =====================================================
       CREATE POST MODAL
    ===================================================== */

    if (openCreateBtn) {

        openCreateBtn.addEventListener("click", () => {

            openModal(createModal);

        });

    }


    if (closeCreateBtn) {

        closeCreateBtn.addEventListener("click", () => {

            closeModal(createModal);

        });

    }


    /* =====================================================
       DETAILS MODAL
    ===================================================== */

    if (closeDetailsBtn) {

        closeDetailsBtn.addEventListener("click", () => {

            closeModal(detailsModal);

        });

    }


    /* =====================================================
       CLOSE WHEN CLICKING OUTSIDE
    ===================================================== */

    [createModal, detailsModal].forEach((modal) => {

        if (!modal) {
            return;
        }

        modal.addEventListener("click", (event) => {

            if (event.target === modal) {

                closeModal(modal);

            }

        });

    });


    /* =====================================================
       ESCAPE KEY
    ===================================================== */

    document.addEventListener("keydown", (event) => {

        if (event.key !== "Escape") {
            return;
        }

        closeModal(createModal);
        closeModal(detailsModal);

    });


    /* =====================================================
       SCHEDULE FIELD
    ===================================================== */

    function updateScheduleVisibility() {

        if (!statusSelect || !scheduleField) {
            return;
        }

        const status = statusSelect.value;

        if (status === "scheduled") {

            scheduleField.style.display = "";

            const input =
                scheduleField.querySelector("input");

            if (input) {
                input.required = true;
            }

        } else {

            scheduleField.style.display = "none";

            const input =
                scheduleField.querySelector("input");

            if (input) {
                input.required = false;
            }

        }

    }


    if (statusSelect) {

        statusSelect.addEventListener(
            "change",
            updateScheduleVisibility
        );

        updateScheduleVisibility();

    }


    /* =====================================================
       LOAD POST DETAILS
    ===================================================== */

    async function loadPostDetails(postId) {

        if (!detailsContent) {
            return;
        }

        detailsContent.innerHTML = `
            <div style="
                padding:40px;
                text-align:center;
                color:#6b7280;
            ">
                Loading post details...
            </div>
        `;

        openModal(detailsModal);

        try {

            const response = await fetch(
                `/publisher/${postId}/details`,
                {
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }

            const data = await response.json();

            renderPostDetails(data);

        } catch (error) {

            console.error(
                "Unable to load post details:",
                error
            );

            detailsContent.innerHTML = `
                <div style="
                    padding:30px;
                    text-align:center;
                    color:#c62828;
                ">
                    Unable to load post details.
                    Please try again.
                </div>
            `;

        }

    }


    /* =====================================================
       RENDER DETAILS
    ===================================================== */

    function renderPostDetails(data) {

        const post = data.post || {};
        const platforms = data.platforms || [];

        const statusClass =
            `publisher-status publisher-status-${escapeHtml(
                post.status || "draft"
            )}`;

        let platformHtml = "";

        if (platforms.length) {

            platformHtml = platforms.map((item) => {

                return `
                    <div class="publisher-platform-detail">

                        <h4>
                            ${escapeHtml(
                                item.platform || "Platform"
                            )}

                            ${
                                item.account_name
                                    ? ` — ${escapeHtml(
                                        item.account_name
                                    )}`
                                    : ""
                            }
                        </h4>

                        <div class="publisher-detail-row">

                            <div class="publisher-detail-label">
                                Username
                            </div>

                            <div class="publisher-detail-value">
                                ${escapeHtml(
                                    item.username || "—"
                                )}
                            </div>

                        </div>

                        <div class="publisher-detail-row">

                            <div class="publisher-detail-label">
                                Platform Status
                            </div>

                            <div class="publisher-detail-value">
                                ${escapeHtml(
                                    item.platform_status || "pending"
                                )}
                            </div>

                        </div>

                        ${
                            item.error_message
                                ? `
                                    <div class="publisher-detail-row">

                                        <div class="publisher-detail-label">
                                            Error
                                        </div>

                                        <div
                                            class="publisher-detail-value"
                                            style="color:#c62828;"
                                        >
                                            ${escapeHtml(
                                                item.error_message
                                            )}
                                        </div>

                                    </div>
                                `
                                : ""
                        }

                    </div>
                `;

            }).join("");

        } else {

            platformHtml = `
                <div style="
                    padding:20px;
                    background:#fafafa;
                    border-radius:10px;
                    color:#6b7280;
                    font-size:13px;
                ">
                    No social accounts are attached to this post.
                </div>
            `;

        }


        detailsContent.innerHTML = `

            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Title
                </div>

                <div class="publisher-detail-value">
                    ${escapeHtml(
                        post.title || "Untitled post"
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Brand
                </div>

                <div class="publisher-detail-value">
                    ${escapeHtml(
                        post.brand_name || "—"
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Status
                </div>

                <div class="publisher-detail-value">
                    <span class="${statusClass}">
                        ${escapeHtml(
                            formatStatus(post.status)
                        )}
                    </span>
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Content
                </div>

                <div class="publisher-detail-value">
                    ${escapeHtml(
                        post.content || "—"
                    ).replace(/\n/g, "<br>")}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Scheduled
                </div>

                <div class="publisher-detail-value">
                    ${formatDate(post.scheduled_at)}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Published
                </div>

                <div class="publisher-detail-value">
                    ${formatDate(post.published_at)}
                </div>

            </div>


            <div style="margin-top:22px;">

                <div style="
                    font-size:13px;
                    font-weight:800;
                    margin-bottom:10px;
                ">
                    Connected Platforms
                </div>

                ${platformHtml}

            </div>
        `;

    }


    /* =====================================================
       DETAILS BUTTONS
    ===================================================== */

    document.addEventListener("click", (event) => {

        const button =
            event.target.closest(
                "[data-post-details]"
            );

        if (!button) {
            return;
        }

        const postId =
            button.getAttribute(
                "data-post-details"
            );

        if (!postId) {
            return;
        }

        loadPostDetails(postId);

    });


    /* =====================================================
       CONFIRM DELETE
    ===================================================== */

    document.addEventListener("submit", (event) => {

        const form =
            event.target.closest(
                "form[data-confirm-delete]"
            );

        if (!form) {
            return;
        }

        const confirmed = window.confirm(
            "Are you sure you want to permanently delete this post?"
        );

        if (!confirmed) {

            event.preventDefault();

        }

    });


    /* =====================================================
       CONFIRM APPROVAL
    ===================================================== */

    document.addEventListener("submit", (event) => {

        const form =
            event.target.closest(
                "form[data-confirm-approval]"
            );

        if (!form) {
            return;
        }

        const confirmed = window.confirm(
            "Submit this post for content approval?"
        );

        if (!confirmed) {

            event.preventDefault();

        }

    });


    /* =====================================================
       CONFIRM STATUS CHANGE
    ===================================================== */

    document.addEventListener("submit", (event) => {

        const form =
            event.target.closest(
                "form[data-confirm-status]"
            );

        if (!form) {
            return;
        }

        const status =
            form.getAttribute(
                "data-confirm-status"
            );

        if (!status) {
            return;
        }

        const confirmed = window.confirm(
            `Change this post status to "${formatStatus(status)}"?`
        );

        if (!confirmed) {

            event.preventDefault();

        }

    });


    /* =====================================================
       STATUS FORMAT
    ===================================================== */

    function formatStatus(status) {

        if (!status) {
            return "Unknown";
        }

        return status
            .replaceAll("_", " ")
            .replace(/\b\w/g, (char) =>
                char.toUpperCase()
            );

    }


    /* =====================================================
       DATE FORMAT
    ===================================================== */

    function formatDate(value) {

        if (!value) {
            return "—";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return escapeHtml(value);
        }

        return date.toLocaleString(
            undefined,
            {
                dateStyle: "medium",
                timeStyle: "short"
            }
        );

    }


    /* =====================================================
       HTML ESCAPE
    ===================================================== */

    function escapeHtml(value) {

        const div =
            document.createElement("div");

        div.textContent =
            value === null || value === undefined
                ? ""
                : String(value);

        return div.innerHTML;

    }

});