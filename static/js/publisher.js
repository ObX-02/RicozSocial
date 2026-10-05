/* =========================================================
   RICOZSOCIAL
   PUBLISHER JAVASCRIPT
   PREMIUM CONTENT WORKSPACE
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTS
    ===================================================== */

    const createModal =
        document.getElementById("createPostModal");

    const detailsModal =
        document.getElementById("postDetailsModal");

    const openCreateBtn =
        document.getElementById("openCreatePost");

    const closeCreateBtn =
        document.getElementById("closeCreatePost");

    const closeDetailsBtn =
        document.getElementById("closePostDetails");

    const statusSelect =
        document.getElementById("publisherStatus");

    const scheduleField =
        document.getElementById("scheduleField");

    const scheduleInput =
        document.getElementById("publisherSchedule");

    const detailsContent =
        document.getElementById("postDetailsContent");


    /* =====================================================
       MODAL CONTROL
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

        const createOpen =
            createModal &&
            createModal.classList.contains("active");

        const detailsOpen =
            detailsModal &&
            detailsModal.classList.contains("active");

        if (!createOpen && !detailsOpen) {
            document.body.style.overflow = "";
        }
    }


    /* =====================================================
       CREATE POST
    ===================================================== */

    function openCreatePostModal() {

        openModal(createModal);

        updateScheduleVisibility();
    }


    function closeCreatePostModal() {

        closeModal(createModal);
    }


    window.openCreatePostModal =
        openCreatePostModal;

    window.closeCreatePostModal =
        closeCreatePostModal;


    if (openCreateBtn) {

        openCreateBtn.addEventListener(
            "click",
            openCreatePostModal
        );
    }


    if (closeCreateBtn) {

        closeCreateBtn.addEventListener(
            "click",
            closeCreatePostModal
        );
    }


    /* =====================================================
       EDIT MODE
    ===================================================== */

    if (
        createModal &&
        createModal.dataset.editMode === "true"
    ) {

        setTimeout(() => {

            openCreatePostModal();

        }, 100);

    }


    /* =====================================================
       DETAILS MODAL
    ===================================================== */

    function closePostDetails() {

        closeModal(detailsModal);
    }


    window.closePostDetails =
        closePostDetails;


    if (closeDetailsBtn) {

        closeDetailsBtn.addEventListener(
            "click",
            closePostDetails
        );
    }


    /* =====================================================
       OUTSIDE CLICK
    ===================================================== */

    [createModal, detailsModal].forEach(
        (modal) => {

            if (!modal) {
                return;
            }

            modal.addEventListener(
                "click",
                (event) => {

                    if (
                        event.target === modal ||
                        event.target.classList.contains(
                            "publisher-modal-overlay"
                        )
                    ) {

                        closeModal(modal);

                    }
                }
            );
        }
    );


    /* =====================================================
       ESCAPE
    ===================================================== */

    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key !== "Escape") {
                return;
            }

            closeModal(createModal);
            closeModal(detailsModal);
        }
    );


    /* =====================================================
       SCHEDULE CONTROL
    ===================================================== */

    function updateScheduleVisibility() {

        if (!statusSelect || !scheduleField) {
            return;
        }

        const status =
            statusSelect.value;

        if (status === "scheduled") {

            scheduleField.style.display = "";

            if (scheduleInput) {
                scheduleInput.required = true;
            }

        } else {

            scheduleField.style.display = "none";

            if (scheduleInput) {
                scheduleInput.required = false;
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
       FORM VALIDATION
    ===================================================== */

    const postForm =
        document.getElementById("publisherPostForm");


    if (postForm) {

        postForm.addEventListener(
            "submit",
            (event) => {

                const brand =
                    document.getElementById(
                        "publisherBrand"
                    );

                const title =
                    document.getElementById(
                        "publisherTitle"
                    );

                const content =
                    document.getElementById(
                        "publisherContent"
                    );


                if (
                    !brand ||
                    !brand.value
                ) {

                    event.preventDefault();

                    alert(
                        "Please select a brand."
                    );

                    brand?.focus();

                    return;
                }


                if (
                    !title ||
                    !title.value.trim()
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter a post title."
                    );

                    title?.focus();

                    return;
                }


                if (
                    !content ||
                    !content.value.trim()
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter post content."
                    );

                    content?.focus();

                    return;
                }


                if (
                    statusSelect &&
                    statusSelect.value === "scheduled"
                ) {

                    if (
                        !scheduleInput ||
                        !scheduleInput.value
                    ) {

                        event.preventDefault();

                        alert(
                            "Please select a future schedule date and time."
                        );

                        scheduleInput?.focus();

                        return;
                    }


                    const selectedDate =
                        new Date(
                            scheduleInput.value
                        );

                    if (
                        Number.isNaN(
                            selectedDate.getTime()
                        )
                    ) {

                        event.preventDefault();

                        alert(
                            "Please select a valid schedule date and time."
                        );

                        return;
                    }


                    if (
                        selectedDate <= new Date()
                    ) {

                        event.preventDefault();

                        alert(
                            "Scheduled time must be in the future."
                        );

                        scheduleInput?.focus();

                        return;
                    }
                }
            }
        );
    }


    /* =====================================================
       AI CONTENT
    ===================================================== */

    function loadAIContentIntoPublisher() {

        const aiContent =
            localStorage.getItem(
                "ricoz_ai_generated_content"
            );

        if (!aiContent) {
            return false;
        }


        const contentField =
            document.getElementById(
                "publisherContent"
            );


        if (!contentField) {
            return false;
        }


        contentField.value =
            aiContent;


        contentField.dispatchEvent(
            new Event(
                "input",
                {
                    bubbles: true
                }
            )
        );


        contentField.focus();


        const status =
            document.getElementById(
                "publisherAIStatus"
            );


        if (status) {

            status.style.display =
                "block";
        }


        localStorage.removeItem(
            "ricoz_ai_generated_content"
        );


        return true;
    }


    function handleAIUseInPost() {

        const aiContent =
            localStorage.getItem(
                "ricoz_ai_generated_content"
            );


        if (!aiContent) {
            return;
        }


        setTimeout(
            () => {

                openCreatePostModal();

                loadAIContentIntoPublisher();

            },
            250
        );
    }


    handleAIUseInPost();


    /* =====================================================
       DETAILS
    ===================================================== */

    async function loadPostDetails(postId) {

        if (!detailsContent) {
            return;
        }


        detailsContent.innerHTML = `
            <div class="publisher-empty">
                <div class="publisher-empty-icon">
                    ...
                </div>
                <h3>
                    Loading post details
                </h3>
                <p>
                    Please wait while the content is loaded.
                </p>
            </div>
        `;


        openModal(detailsModal);


        try {

            const response =
                await fetch(
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


            const data =
                await response.json();


            renderPostDetails(data);


        } catch (error) {

            console.error(
                "Unable to load post details:",
                error
            );


            detailsContent.innerHTML = `
                <div class="publisher-empty">

                    <div class="publisher-empty-icon">
                        !
                    </div>

                    <h3>
                        Unable to load details
                    </h3>

                    <p>
                        Please try again.
                    </p>

                </div>
            `;
        }
    }


    window.viewPostDetails =
        loadPostDetails;


    /* =====================================================
       RENDER DETAILS
    ===================================================== */

    function renderPostDetails(data) {

        const post =
            data.post || {};

        const platforms =
            data.platforms || [];


        const detailsTitle =
            document.getElementById(
                "detailsTitle"
            );


        if (detailsTitle) {

            detailsTitle.textContent =
                post.title ||
                "Post Details";
        }


        const status =
            post.status ||
            "draft";


        const statusClass =
            `publisher-status publisher-status-${escapeHtml(
                status.replaceAll("_", "-")
            )}`;


        let platformHtml = "";


        if (platforms.length) {

            platformHtml =
                platforms
                    .map(
                        (item) => {

                            return `
                                <div class="publisher-platform-detail">

                                    <h4>
                                        ${escapeHtml(
                                            item.platform ||
                                            "Platform"
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
                                                item.username ||
                                                "—"
                                            )}
                                        </div>

                                    </div>


                                    <div class="publisher-detail-row">

                                        <div class="publisher-detail-label">
                                            Platform Status
                                        </div>

                                        <div class="publisher-detail-value">
                                            ${escapeHtml(
                                                item.platform_status ||
                                                "pending"
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
                                                        style="color:#c91f2b;"
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
                        }
                    )
                    .join("");

        } else {

            platformHtml = `
                <div class="publisher-no-accounts">

                    <strong>
                        No social accounts attached
                    </strong>

                    <span>
                        This post has no connected platform accounts.
                    </span>

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
                        post.title ||
                        "Untitled post"
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Brand
                </div>

                <div class="publisher-detail-value">
                    ${escapeHtml(
                        post.brand_name ||
                        "—"
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Created By
                </div>

                <div class="publisher-detail-value">
                    ${escapeHtml(
                        post.creator_name ||
                        "—"
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
                            formatStatus(status)
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
                        post.content ||
                        "—"
                    ).replace(
                        /\n/g,
                        "<br>"
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Scheduled
                </div>

                <div class="publisher-detail-value">
                    ${formatDate(
                        post.scheduled_at
                    )}
                </div>

            </div>


            <div class="publisher-detail-row">

                <div class="publisher-detail-label">
                    Published
                </div>

                <div class="publisher-detail-value">
                    ${formatDate(
                        post.published_at
                    )}
                </div>

            </div>


            <div style="margin-top:22px;">

                <div
                    style="
                        font-size:13px;
                        font-weight:900;
                        color:#17191d;
                        margin-bottom:10px;
                    "
                >
                    Connected Platforms
                </div>

                ${platformHtml}

            </div>
        `;
    }


    /* =====================================================
       DELETE CONFIRMATION
    ===================================================== */

    document.addEventListener(
        "submit",
        (event) => {

            const form =
                event.target.closest(
                    "form[data-confirm-delete]"
                );


            if (!form) {
                return;
            }


            const confirmed =
                window.confirm(
                    "Are you sure you want to permanently delete this post?"
                );


            if (!confirmed) {

                event.preventDefault();
            }
        }
    );


    /* =====================================================
       APPROVAL CONFIRMATION
    ===================================================== */

    document.addEventListener(
        "submit",
        (event) => {

            const form =
                event.target.closest(
                    "form[data-confirm-approval]"
                );


            if (!form) {
                return;
            }


            const confirmed =
                window.confirm(
                    "Submit this post for content approval?"
                );


            if (!confirmed) {

                event.preventDefault();
            }
        }
    );


    /* =====================================================
       STATUS CONFIRMATION
    ===================================================== */

    document.addEventListener(
        "submit",
        (event) => {

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


            const confirmed =
                window.confirm(
                    `Change this post status to "${formatStatus(status)}"?`
                );


            if (!confirmed) {

                event.preventDefault();
            }
        }
    );


    /* =====================================================
       STATUS FORMAT
    ===================================================== */

    function formatStatus(status) {

        if (!status) {
            return "Unknown";
        }


        return String(status)
            .replaceAll("_", " ")
            .replace(
                /\b\w/g,
                (char) =>
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


        const date =
            new Date(value);


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {

            return escapeHtml(
                value
            );
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
            document.createElement(
                "div"
            );


        div.textContent =
            value === null ||
            value === undefined
                ? ""
                : String(value);


        return div.innerHTML;
    }

});