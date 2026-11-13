const resumeInput = document.getElementById("resumes");
const fileList = document.getElementById("file-list");
const setupForm = document.getElementById(".setup-card");

if (resumeInput && fileList) {
    resumeInput.addEventListener("change", () => {
        fileList.replaceChildren();

        const files = [...resumeInput.files];

        if(files.length === 0) {
            return;
        }

        const count = document.createElement("strong");
        count.className = "file-count";
        count.textContent = `${files.length} file${files.length === 1 ? "" : "s"} selected`;        
        fileList.append(count);

        const names = document.createElement("ul");
        names.className = "file-names";

        files.forEach(file => {
            const item = document.createElement("li");
            item.textContent = file.name;
            names.append(item);
        });

        fileList.append(names);
    });
}

if (setupForm) {
    setupForm.addEventListener("submit", () => {
        const button = setupForm.querySelector('button[type="submit"]');

        if(button) {
            button.disabled = true;
            button.querySelector(".button-label").textContent = "Reading resumes...";
        }
    });

}