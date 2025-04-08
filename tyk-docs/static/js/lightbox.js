document.addEventListener("DOMContentLoaded", function () {
    // Create the modal elements
    let modal = document.createElement("div");
    modal.style.position = "fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100%";
    modal.style.height = "100%";
    modal.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
    modal.style.display = "none";
    modal.style.justifyContent = "center";
    modal.style.alignItems = "center";
    modal.style.cursor = "pointer";

    let img = document.createElement("img");
    img.style.maxWidth = "90%";
    img.style.maxHeight = "90%";

    let closeButton = document.createElement("span");
    closeButton.innerHTML = "&times;";
    closeButton.style.position = "absolute";
    closeButton.style.top = "10px";
    closeButton.style.right = "20px";
    closeButton.style.fontSize = "30px";
    closeButton.style.color = "white";
    closeButton.style.cursor = "pointer";

    modal.appendChild(img);
    modal.appendChild(closeButton);
    document.body.appendChild(modal);

    // Set cursor style for all images in main-content
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
        // Add pointer cursor to all images in main-content that are not inside anchor tags
        const contentImages = mainContent.querySelectorAll("img");
        contentImages.forEach(image => {
            // Check if the image is not inside an anchor tag
            if (!image.closest('a')) {
                image.style.cursor = "pointer";
            }
        });

        mainContent.addEventListener("click", function (event) {
            if (event.target.tagName === "IMG" && event.target !== img) {
                // Check if the clicked image is not inside an anchor tag
                if (!event.target.closest('a')) {
                    img.src = event.target.src;
                    modal.style.display = "flex";
                }
            }
        });
    }

    // Close modal when clicked (but not when clicking the image itself)
    modal.addEventListener("click", function (event) {
        if (event.target !== img) {
            modal.style.display = "none";
        }
    });

    // Close modal when clicking the close button
    closeButton.addEventListener("click", function (event) {
        modal.style.display = "none";
        event.stopPropagation(); // Prevent modal click from triggering
    });

    // Close modal when pressing the Escape key
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modal.style.display === "flex") {
            modal.style.display = "none";
        }
    });
});
