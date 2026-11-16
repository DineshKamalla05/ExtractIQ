const MAX_FILE_SIZE = 10 * 1024 * 1024;
const fileInput = document.getElementById("pdfFile");
const dropzone = document.getElementById("dropzone");
const statusElement = document.getElementById("status");

fileInput.addEventListener("change", () => updateSelectedFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("is-dragging");
    });
});
["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("is-dragging");
    });
});
dropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (file) {
        fileInput.files = event.dataTransfer.files;
        updateSelectedFile(file);
    }
});

function updateSelectedFile(file) {
    const selected = document.getElementById("selectedFile");
    const label = document.getElementById("fileLabel");
    if (!file) return;
    label.textContent = file.name;
    selected.hidden = false;
    selected.textContent = `${formatBytes(file.size)} · ready to process`;
}

async function uploadPDF() {
    const file = fileInput.files[0];
    const result = document.getElementById("result");
    const button = document.getElementById("uploadButton");

    if (!file) return showStatus("Choose a PDF before extracting.", true);
    if (!file.name.toLowerCase().endsWith(".pdf")) return showStatus("Only PDF files are supported.", true);
    if (file.size > MAX_FILE_SIZE) return showStatus("PDF must be smaller than 10 MB.", true);

    button.disabled = true;
    button.textContent = "Analyzing PDF...";
    showStatus("Reading your document...");
    result.className = "empty-state loading";
    result.innerHTML = "<span class=\"spinner\"></span><strong>Extracting insights</strong><span>This usually takes a few seconds.</span>";

    try {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch("/upload", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Upload failed");
        showStatus("PDF processed successfully.");
        result.className = "profile-result";
        result.innerHTML = renderInformation(data);
        loadDocuments();
    } catch (error) {
        showStatus(error.message, true);
        result.className = "empty-state";
        result.innerHTML = "<span class=\"empty-icon\">!</span><strong>We could not process that file</strong><span>Check the PDF and try again.</span>";
    } finally {
        button.disabled = false;
        button.textContent = "Extract PDF";
    }
}

function renderInformation(data) {
    const info = data.extracted_information;
    const skills = info.skills.length
        ? info.skills.map((skill) => `<span class="skill">${escapeHtml(skill)}</span>`).join("")
        : "<span class=\"muted\">No skills detected</span>";
    return `<div class="profile-header"><div class="avatar">${escapeHtml((info.name || "?").charAt(0).toUpperCase())}</div><div><h3>${escapeHtml(info.name || "Document information")}</h3><span class="profile-label">Detected document information</span></div></div>
        <div class="contact-grid"><div><small>EMAIL</small><span>${escapeHtml(info.email || "Not found")}</span></div><div><small>PHONE</small><span>${escapeHtml(info.phone || "Not found")}</span></div><div><small>PAGES</small><span>${data.page_count}</span></div></div>
        <div class="skills-block"><small>DETECTED SKILLS</small><div class="skills">${skills}</div></div>
        <details><summary>View extracted text</summary><pre>${escapeHtml(data.extracted_text || "No text found")}</pre></details>`;
}

function showStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.className = `status ${isError ? "error" : "success"}`;
}

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value);
    return element.innerHTML;
}

function formatBytes(bytes) {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

async function loadDocuments() {
    const response = await fetch("/documents");
    if (!response.ok) return;
    const data = await response.json();
    const history = document.getElementById("history");
    const count = data.documents.length;
    document.getElementById("documentCount").textContent = `${count} file${count === 1 ? "" : "s"}`;
    history.innerHTML = data.documents.map((doc) =>
        `<li><span class="file-icon">PDF</span><div class="history-name"><strong>${escapeHtml(doc.filename)}</strong><small>${doc.page_count} page${doc.page_count === 1 ? "" : "s"}</small></div><button class="delete-button" onclick="deleteDocument(${doc.id})" aria-label="Delete ${escapeHtml(doc.filename)}">Delete</button></li>`
    ).join("") || "<li class=\"history-empty\">No documents uploaded yet.</li>";
}

async function deleteDocument(id) {
    const response = await fetch(`/documents/${id}`, { method: "DELETE" });
    if (response.ok) loadDocuments();
}

loadDocuments();
