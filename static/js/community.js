/* =========================================================
   RICOZSOCIAL
   ENGAGEMENT / COMMUNITY JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const commentCards = document.querySelectorAll(
        ".engagement-comment-card"
    );

    const detailContainer = document.getElementById(
        "engagement-detail"
    );

    if (!commentCards.length || !detailContainer) {
        return;
    }


    /* =====================================================
       HELPERS
    ===================================================== */

    function escapeHtml(value) {

        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function getInitial(name) {

        if (!name) {
            return "U";
        }

        return String(name)
            .trim()
            .charAt(0)
            .toUpperCase();
    }


    function getStatusClass(status) {

        const normalized = String(status || "pending")
            .toLowerCase();

        if (
            normalized === "resolved" ||
            normalized === "replied"
        ) {
            return "status-" + normalized;
        }

        return "status-pending";
    }


    function getStatusLabel(status) {

        if (!status) {
            return "Pending";
        }

        return String(status)
            .replace(/_/g, " ")
            .replace(/\b\w/g, function (letter) {
                return letter.toUpperCase();
            });
    }


    /* =====================================================
       DETAIL PANEL
    ===================================================== */

    function renderConversation(card) {

        const id = card.dataset.commentId || "";

        const author =
            card.dataset.author || "Unknown User";

        const username =
            card.dataset.username || "";

        const content =
            card.dataset.content || "No comment content available.";

        const status =
            card.dataset.status || "pending";

        const brand =
            card.dataset.brand || "Unassigned";

        const platform =
            card.dataset.platform || "Unknown";

        const account =
            card.dataset.account || "";

        const reply =
            card.dataset.reply || "";

        const created =
            card.dataset.created || "Unknown date";


        const usernameHtml = username
            ? "@" + escapeHtml(username)
            : "Community member";


        const accountHtml = account
            ? escapeHtml(account)
            : "Connected account";


        let replyHtml = "";

        if (reply.trim()) {

            replyHtml = `
                <div class="engagement-existing-reply">

                    <div class="engagement-existing-reply-label">
                        Your Reply
                    </div>

                    <div class="engagement-existing-reply-text">
                        ${escapeHtml(reply)}
                    </div>

                </div>
            `;

        }


        detailContainer.innerHTML = `

            <div class="engagement-detail-header">

                <div class="engagement-detail-person">

                    <div class="engagement-detail-avatar">
                        ${escapeHtml(getInitial(author))}
                    </div>

                    <div>

                        <strong>
                            ${escapeHtml(author)}
                        </strong>

                        <span>
                            ${usernameHtml}
                        </span>

                    </div>

                </div>

                <span class="
                    engagement-detail-status
                    ${getStatusClass(status)}
                ">
                    ${escapeHtml(getStatusLabel(status))}
                </span>

            </div>


            <div class="engagement-detail-meta">

                <span>
                    ${escapeHtml(platform)}
                </span>

                <span>•</span>

                <span>
                    ${escapeHtml(brand)}
                </span>

                <span>•</span>

                <span>
                    ${accountHtml}
                </span>

                <span>•</span>

                <span>
                    ${escapeHtml(created)}
                </span>

            </div>


            <div class="engagement-conversation-area">

                <div class="engagement-message-label">
                    Community Message
                </div>

                <div class="engagement-message">
                    ${escapeHtml(content)}
                </div>

                <div class="engagement-message-time">
                    Received ${escapeHtml(created)}
                </div>

                ${replyHtml}

            </div>


            <div class="engagement-reply-area">

                <form
                    method="POST"
                    action="/community/${id}/reply"
                    class="engagement-reply-form"
                >

                    <label
                        class="engagement-reply-label"
                        for="engagement-reply-input"
                    >
                        Write a reply
                    </label>

                    <textarea
                        id="engagement-reply-input"
                        name="reply"
                        class="engagement-reply-textarea"
                        maxlength="5000"
                        placeholder="Write a professional response to this community message..."
                    ></textarea>

                    <div class="engagement-reply-bottom">

                        <span class="engagement-reply-hint">
                            Keep responses clear, helpful and professional.
                        </span>

                        <div class="engagement-reply-actions">

                            <button
                                type="submit"
                                class="engagement-reply-button"
                            >
                                Send Reply
                            </button>

                        </div>

                    </div>

                </form>


                <div class="engagement-reply-bottom">

                    <span class="engagement-reply-hint">
                        Conversation status
                    </span>

                    <div class="engagement-reply-actions">

                        <form
                            method="POST"
                            action="/community/${id}/resolve"
                            onsubmit="return confirm('Mark this conversation as resolved?');"
                        >

                            <button
                                type="submit"
                                class="engagement-resolve-button"
                            >
                                ✓ Resolve Conversation
                            </button>

                        </form>

                    </div>

                </div>

            </div>
        `;


        const textarea = document.getElementById(
            "engagement-reply-input"
        );

        if (textarea) {

            textarea.addEventListener(
                "input",
                function () {

                    const remaining =
                        5000 - this.value.length;

                    const hint =
                        this
                            .closest(".engagement-reply-form")
                            ?.querySelector(
                                ".engagement-reply-hint"
                            );

                    if (hint) {

                        hint.textContent =
                            `${remaining} characters remaining`;

                    }

                }
            );

        }

    }


    /* =====================================================
       SELECT CONVERSATION
    ===================================================== */

    commentCards.forEach(function (card) {

        card.addEventListener("click", function () {

            commentCards.forEach(function (item) {
                item.classList.remove("active");
            });

            card.classList.add("active");

            renderConversation(card);

        });

    });


    /* =====================================================
       LOAD FIRST CONVERSATION
    ===================================================== */

    renderConversation(commentCards[0]);


    /* =====================================================
       KEYBOARD ACCESSIBILITY
    ===================================================== */

    commentCards.forEach(function (card) {

        card.setAttribute(
            "tabindex",
            "0"
        );

        card.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    card.click();

                }

            }
        );

    });

});