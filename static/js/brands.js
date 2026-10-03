/* =========================================================
   RICOZSOCIAL
   BRANDS INTERACTIONS
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const createModal =
        document.getElementById("createBrandModal");

    const editModal =
        document.getElementById("editBrandModal");


    /* =====================================================
       CREATE MODAL
    ===================================================== */

    const openCreateButtons =
        document.querySelectorAll(
            "[data-open-brand-modal]"
        );

    const closeCreateButtons =
        document.querySelectorAll(
            "[data-close-brand-modal]"
        );


    function openCreateModal() {

        if (!createModal) {
            return;
        }

        createModal.classList.add("is-open");
        createModal.setAttribute(
            "aria-hidden",
            "false"
        );

        const input =
            document.getElementById("brandName");

        if (input) {
            setTimeout(() => input.focus(), 100);
        }

        document.body.classList.add(
            "modal-open"
        );
    }


    function closeCreateModal() {

        if (!createModal) {
            return;
        }

        createModal.classList.remove("is-open");
        createModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );
    }


    openCreateButtons.forEach((button) => {
        button.addEventListener(
            "click",
            openCreateModal
        );
    });


    closeCreateButtons.forEach((button) => {
        button.addEventListener(
            "click",
            closeCreateModal
        );
    });


    if (createModal) {

        createModal.addEventListener(
            "click",
            (event) => {

                if (
                    event.target === createModal
                ) {
                    closeCreateModal();
                }

            }
        );

    }


    /* =====================================================
       EDIT MODAL
    ===================================================== */

    const openEditButton =
        document.querySelector(
            "[data-open-edit-modal]"
        );

    const closeEditButtons =
        document.querySelectorAll(
            "[data-close-edit-modal]"
        );


    function openEditModal() {

        if (!editModal) {
            return;
        }

        editModal.classList.add("is-open");
        editModal.setAttribute(
            "aria-hidden",
            "false"
        );

        const input =
            document.getElementById(
                "editBrandName"
            );

        if (input) {
            setTimeout(() => input.focus(), 100);
        }

        document.body.classList.add(
            "modal-open"
        );
    }


    function closeEditModal() {

        if (!editModal) {
            return;
        }

        editModal.classList.remove("is-open");
        editModal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "modal-open"
        );
    }


    if (openEditButton) {

        openEditButton.addEventListener(
            "click",
            openEditModal
        );

    }


    closeEditButtons.forEach((button) => {

        button.addEventListener(
            "click",
            closeEditModal
        );

    });


    if (editModal) {

        editModal.addEventListener(
            "click",
            (event) => {

                if (
                    event.target === editModal
                ) {
                    closeEditModal();
                }

            }
        );

    }


    /* =====================================================
       ESC KEY
    ===================================================== */

    document.addEventListener(
        "keydown",
        (event) => {

            if (event.key !== "Escape") {
                return;
            }

            closeCreateModal();
            closeEditModal();

        }
    );


    /* =====================================================
       ENTERPRISE SEARCH
    ===================================================== */

    const searchInput =
        document.querySelector(
            ".brand-search input"
        );

    if (searchInput) {

        searchInput.addEventListener(
            "keydown",
            (event) => {

                if (event.key === "Enter") {

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
       AUTO OPEN AFTER VALIDATION ERROR
    ===================================================== */

    if (
        createModal &&
        createModal.dataset.open === "true"
    ) {
        openCreateModal();
    }

});