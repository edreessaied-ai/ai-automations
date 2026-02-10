/*
    Contains the logic for the ticket drafter form.
    Handles support for creating new drafts and editing existing ones.
*/

// URL to fetch existing draft data for editing
const BASE_FORM_URL = "https://dev.aiautomations.engineering/";
const FORM_SUBMISSION_URL = "https://edreessaied.app.n8n.cloud/webhook/form-submission";

// Fetch params in the URL
const params = new URLSearchParams(window.location.search);
const state = params.get("state");
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

async function loadTicketDraftFormFromEditToken(editToken) {
    // Load the draft data from the server
    try {
        const res = await fetch(`${FORM_SUBMISSION_URL}?editToken=${encodeURIComponent(editToken)}`);
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
        document.getElementById("aiTicketDrafterEnabled").value = data.aiTicketDrafterEnabled ? "Yes" : "No";

        // Show form
        show("state-new");
    } catch (err) {
        console.error(err);
        show("state-unknown");
    }
}

// If there's no state, show the new form. 
// If it's "submitted", show the submitted state.
// If it's "edit", load the draft for editing.
// Otherwise, show an error.
if (!state) {
    // New form
    show("state-new");
} else if (state === "submitted") {
    // Show submitted state
    document.getElementById("new-form").href = BASE_FORM_URL;
    const editButtonElement = document.getElementById("edit-form");
    // if there's an edit button, set the href to include the edit token,
    // otherwise disable the edit link
    if (editButtonElement) {
        if (editToken) {
            editButtonElement.href =
                `${BASE_FORM_URL}?state=edit&editToken=${encodeURIComponent(editToken)}`;
        } else {
            editButtonElement.classList.add("disabled");
            editButtonElement.removeAttribute("href");
        }
    }
    show("state-submitted");
} else if (state === "edit") {
    // Load edited draft
    loadTicketDraftFormFromEditToken(editToken);
} else {
    // Invalid state
    show("state-unknown");
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