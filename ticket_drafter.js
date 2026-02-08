/*
    Contains the logic for the ticket drafter form.
    Handles support for creating new drafts and editing existing ones.
*/

// URL to fetch existing draft data for editing
const FORM_SUBMISSION_URL = "https://edreessaied.app.n8n.cloud/webhook/form-submission";

// Fetch params in the URL
const params = new URLSearchParams(window.location.search);
// Parse the edit token if present
const editToken = params.get("editToken");

// Hide all sections
document.querySelectorAll("section").forEach(el => el.classList.add("hidden"));

function show(element_id) {
    // Show the specified section
    const element = document.getElementById(element_id);
    if (element) {
        element.classList.remove("hidden");
    }
}

async function loadDraft(token) {
    // Load the draft data from the server
    try {
        const res = await fetch(`${FORM_SUBMISSION_URL}?editToken=${encodeURIComponent(token)}`);
        if (!res.ok) {
            throw new Error("Ticket draft not found");
        }
        const data = await res.json();

        // Populate fields
        document.getElementById("ticketTitle").value = data.ticketTitle || "";
        document.getElementById("ticketDescription").value = data.ticketDescription || "";
        document.getElementById("ticketType").value = data.ticketType || "";
        document.getElementById("ticketImpact").value = data.ticketImpact || "";
        document.getElementById("assigneeTeam").value = data.assigneeTeam || "";
        document.getElementById("assignee").value = data.assignee || "";
        document.getElementById("userEmail").value = data.userEmail || "";
        document.getElementById("aiTicketDrafterEnabled").value = data.aiTicketDrafterEnabled || "";

        // Show form
        show("state-new");
    } catch (err) {
        console.error(err);
        show("state-invalid-edit");
    }
}

// Show the populated form if we have an edit token, otherwise show the blank form
if (!editToken) {
    // New form
    show("state-new");
} else {
    // Load draft
    loadDraft(editToken);
}

// ===== Fullscreen textarea handler =====
const textarea = document.getElementById("ticketDescription");
let anchor = null;
textarea.addEventListener("dblclick", () => {
    const isFullscreen = textarea.classList.contains("fullscreen-textarea");
    if (!isFullscreen) {
    if (!anchor) {
        const rect = textarea.getBoundingClientRect();
        anchor = { width: textarea.style.width || rect.width + "px", height: textarea.style.height || rect.height + "px" };
    }
    textarea.classList.add("fullscreen-textarea");
    } else {
    textarea.classList.remove("fullscreen-textarea");
    textarea.style.width = anchor.width;
    textarea.style.height = anchor.height;
    }
    textarea.focus();
});