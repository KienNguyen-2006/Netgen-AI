document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");
    const uploadBtn = document.getElementById("upload-btn");

    if (!dropZone) return;

    dropZone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            const name = fileInput.files[0].name;
            fileNameDisplay.textContent = name;
            uploadBtn.disabled = false;
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");

        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.endsWith(".csv")) {
            fileInput.files = files;
            fileNameDisplay.textContent = files[0].name;
            uploadBtn.disabled = false;
        } else {
            fileNameDisplay.textContent = "Please drop a .csv file";
            fileNameDisplay.style.color = "#dc2626";
        }
    });

    // Auto-dismiss flash messages after 8 seconds
    document.querySelectorAll(".flash").forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = "0";
            flash.style.transform = "translateY(-8px)";
            setTimeout(() => flash.remove(), 300);
        }, 8000);
    });
});
