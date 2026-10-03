/* =========================================================
   RICOZSOCIAL
   SOCIAL ACCOUNTS
   PAGE INTERACTIONS
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("accountModal");

    const openButton = document.getElementById("openAccountModal");
    const openEmptyButton = document.getElementById("openAccountModalEmpty");

    const closeButton = document.getElementById("closeAccountModal");
    const cancelButton = document.getElementById("cancelAccountModal");


    /* =====================================================
       SAFETY CHECK
    ====================================================== */

    if (!modal) {
        return;
    }


    /* =====================================================
       OPEN MODAL
    ====================================================== */

    const openModal = () => {

        modal.classList.add("is-open");

        modal.setAttribute("aria-hidden", "false");

        document.body.classList.add("modal-open");

        const firstInput = modal.querySelector(
            "select, input, textarea"
        );

        if (firstInput) {
            setTimeout(() => {
                firstInput.focus();
            }, 100);
        }
    };


    /* =====================================================
       CLOSE MODAL
    ====================================================== */

    const closeModal = () => {

        modal.classList.remove("is-open");

        modal.setAttribute("aria-hidden", "true");

        document.body.classList.remove("modal-open");
    };


    /* =====================================================
       OPEN BUTTON
    ====================================================== */

    if (openButton) {

        openButton.addEventListener("click", () => {
            openModal();
        });

    }


    /* =====================================================
       EMPTY STATE OPEN BUTTON
    ====================================================== */

    if (openEmptyButton) {

        openEmptyButton.addEventListener("click", () => {
            openModal();
        });

    }


    /* =====================================================
       CLOSE BUTTON
    ====================================================== */

    if (closeButton) {

        closeButton.addEventListener("click", () => {
            closeModal();
        });

    }


    /* =====================================================
       CANCEL BUTTON
    ====================================================== */

    if (cancelButton) {

        cancelButton.addEventListener("click", () => {
            closeModal();
        });

    }


    /* =====================================================
       CLICK OUTSIDE MODAL
    ====================================================== */

    modal.addEventListener("click", (event) => {

        if (event.target === modal) {
            closeModal();
        }

    });


    /* =====================================================
       ESCAPE KEY
    ====================================================== */

    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {

            if (modal.classList.contains("is-open")) {
                closeModal();
            }

        }

    });


    /* =====================================================
       PREVENT MODAL BACKGROUND SCROLL
    ====================================================== */

    modal.addEventListener("wheel", (event) => {

        const modalBox = modal.querySelector(".account-modal");

        if (!modalBox) {
            return;
        }

        const atTop = modalBox.scrollTop === 0;

        const atBottom =
            modalBox.scrollTop + modalBox.clientHeight >=
            modalBox.scrollHeight - 1;

        if (
            (event.deltaY < 0 && atTop) ||
            (event.deltaY > 0 && atBottom)
        ) {
            event.preventDefault();
        }

    }, { passive: false });


    /* =====================================================
       FORM DOUBLE-SUBMIT PROTECTION
    ====================================================== */

    const accountForm = modal.querySelector(".account-form");

    if (accountForm) {

        accountForm.addEventListener("submit", () => {

            const submitButton = accountForm.querySelector(
                'button[type="submit"]'
            );

            if (!submitButton) {
                return;
            }

            submitButton.disabled = true;

            submitButton.style.opacity = "0.65";

            submitButton.style.cursor = "wait";

            submitButton.textContent = "Adding...";

        });

    }

});