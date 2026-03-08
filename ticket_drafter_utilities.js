/*
    Ticket Drafter Utilities
    Contains utility functions and error classes for the ticket drafter application.
*/

import {
    validateTicketDraftData,
    TicketDraftSchemaValidationError,
} from "./ticket_schema.js"


export class TicketDraftError extends Error {
  constructor(message) {
    super(message);
    this.name = "TicketDraftError";
  }
}

export class TicketDraftDataFetchError extends TicketDraftError {
  constructor(message) {
    super(message);
    this.name = "TicketDraftDataFetchError";
  }
}


// URLs to send or fetch ticket draft data
export const FRONTEND_FORM_LINK = "https://dev.aiautomations.engineering/";
export const FORM_SUBMISSION_WEBHOOK_TO_BACKEND = "https://edreessaied.app.n8n.cloud/webhook/form-submission";



 // ===== UI Utility functions =====

export function hideAllStates() {
    /* 
        Power to hide all sections on the page,
        used before showing a specific section
    */
    document.querySelectorAll("section")
        .forEach(el => el.classList.add("hidden"));
}


export function showPageState(element_id) {
    /*
        Show a specific section by ID and hide all others
    */
    const element = document.getElementById(element_id);
    if (element) {
        hideAllStates();
        element.classList.remove("hidden");
    }

    if (element === "form-state") {
        initializeFormUI();
    }
}


export async function loadTicketDraftFormFromEditToken(editToken, options = {}) {
    /*
        Load existing ticket draft data from server using the edit token,
        and populate the form fields for editing.
        
        Implements a retry mechanism to handle potential delays in
        data availability after form submission.
    */

    const {
        retries = 10,
        retryDelayMs = 1000,
    } = options;

    const webhookUrl = `${FORM_SUBMISSION_WEBHOOK_TO_BACKEND}?editToken=${encodeURIComponent(editToken)}`;

    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const webhookResponse = await fetch(webhookUrl);

            if (!webhookResponse.ok) {
                throw new TicketDraftDataFetchError(
                    `Backend request failed: ${webhookResponse.status}`
                );
            }
            // Load the response text and check if it's empty before parsing
            const responseText = await webhookResponse.text();
            if (!responseText) {
                throw new TicketDraftDataFetchError(
                    `Backend returned an empty response, data might not be available`
                );
            }

            // Parse and validate the response data
            const webhookData = JSON.parse(responseText);
            // Validate data response of N8N workflow
            validateTicketDraftData(webhookData);

            // Populate fields
            const formResponse = webhookData[0];
            document.getElementById("ticketTitle").value = formResponse.ticketTitle || "";
            document.getElementById("ticketDescription").value = formResponse.ticketDescription || "";
            document.getElementById("ticketType").value = formResponse.ticketType || "";
            document.getElementById("ticketImpact").value = formResponse.ticketImpact || "";
            document.getElementById("assigneeTeam").value = formResponse.assigneeTeam || "";
            document.getElementById("assignee").value = formResponse.assignee || "";
            document.getElementById("userEmail").value = formResponse.userEmail || "";
            document.getElementById("aiTicketDrafterEnabled").value = formResponse.aiTicketDrafterEnabled || "";

            showPageState("form-state");
            break; // Exit loop on success
        } catch (err) {
            if (attempt === retries) {
                throw new TicketDraftError("Failed to load ticket draft data from server.");
            }
            console.error("Failed to load ticket draft data; retrying... ", err);
            await new Promise(resolve => setTimeout(resolve, retryDelayMs));
        }
    }
}


export function initializeFormUI() {
    /* 
        Fullscreen ticket description box handler
    */
    const textarea = document.getElementById("ticketDescription");
    if (!textarea) return;

    let anchor = null;

    textarea.addEventListener("dblclick", () => {
        const isFullscreen = textarea.classList.contains("fullscreen-textarea");

        if (!isFullscreen) {
            if (!anchor) {
                const rect = textarea.getBoundingClientRect();
                anchor = {
                    width: textarea.style.width || rect.width + "px",
                    height: textarea.style.height || rect.height + "px"
                };
            }
            textarea.classList.add("fullscreen-textarea");
        } else {
            textarea.classList.remove("fullscreen-textarea");
            textarea.style.width = anchor.width;
            textarea.style.height = anchor.height;
        }

        textarea.focus();
    });
}