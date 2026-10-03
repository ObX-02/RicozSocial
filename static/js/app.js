/* =========================================================
   RICOZ SOCIAL
   GLOBAL APPLICATION JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       SIDEBAR
    ===================================================== */

    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const mobileMenuButton = document.getElementById(
        "mobileMenuButton"
    );
    const sidebarClose = document.getElementById(
        "sidebarClose"
    );


    function openSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.add("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.add("open");
        }

        document.body.style.overflow = "hidden";
    }


    function closeSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.remove("open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.remove("open");
        }

        document.body.style.overflow = "";
    }


    if (mobileMenuButton) {

        mobileMenuButton.addEventListener(
            "click",
            openSidebar
        );

    }


    if (sidebarClose) {

        sidebarClose.addEventListener(
            "click",
            closeSidebar
        );

    }


    if (sidebarOverlay) {

        sidebarOverlay.addEventListener(
            "click",
            closeSidebar
        );

    }


    /* =====================================================
       CLOSE MOBILE SIDEBAR AFTER NAVIGATION
    ===================================================== */

    document
        .querySelectorAll(".nav-item")
        .forEach((item) => {

            item.addEventListener(
                "click",
                closeSidebar
            );

        });


    /* =====================================================
       USER DROPDOWN
    ===================================================== */

    const userMenuButton = document.getElementById(
        "userMenuButton"
    );

    const userDropdown = document.getElementById(
        "userDropdown"
    );


    if (userMenuButton && userDropdown) {

        userMenuButton.addEventListener(
            "click",
            (event) => {

                event.stopPropagation();

                userDropdown.classList.toggle(
                    "open"
                );

            }
        );


        document.addEventListener(
            "click",
            (event) => {

                if (
                    !userDropdown.contains(event.target) &&
                    !userMenuButton.contains(event.target)
                ) {

                    userDropdown.classList.remove(
                        "open"
                    );

                }

            }
        );

    }


    /* =====================================================
       FLASH MESSAGE CLOSE
    ===================================================== */

    document
        .querySelectorAll(".flash-close")
        .forEach((button) => {

            button.addEventListener(
                "click",
                () => {

                    const message =
                        button.closest(
                            ".flash-message"
                        );

                    if (message) {

                        message.style.opacity = "0";

                        message.style.transform =
                            "translateY(-4px)";

                        setTimeout(() => {

                            message.remove();

                        }, 180);

                    }

                }
            );

        });


    /* =====================================================
       SEARCH BUTTON
    ===================================================== */

    const searchButton = document.getElementById(
        "searchButton"
    );


    if (searchButton) {

        searchButton.addEventListener(
            "click",
            () => {

                alert(
                    "Global search will be available with the upcoming search module."
                );

            }
        );

    }


    /* =====================================================
       AUTO HIDE FLASH MESSAGES
    ===================================================== */

    setTimeout(() => {

        document
            .querySelectorAll(
                ".flash-message"
            )
            .forEach((message) => {

                message.style.opacity = "0";

                message.style.transform =
                    "translateY(-4px)";

                setTimeout(() => {

                    message.remove();

                }, 180);

            });

    }, 6000);

});