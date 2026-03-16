/*
    Ticket Drafter Utilities
    Contains utility functions and error classes for the ticket drafter application.
*/

import {
    validateTicketDraftData,
    TicketDraftSchemaValidationError,
    type TicketDraftData,
} from "./ticket_schema.js"

// Custom error classes for better error handling and debugging

export class TicketDraftError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TicketDraftError";
  }
}

export class TicketDraftDataFetchError extends TicketDraftError {
  constructor(message: string) {
    super(message);
    this.name = "TicketDraftDataFetchError";
  }
}


// URLs to send or fetch ticket draft data
export const FRONTEND_FORM_LINK = "https://dev.aiautomations.engineering/";
export const FORM_SUBMISSION_WEBHOOK_TO_BACKEND = "https://edreessaied.app.n8n.cloud/webhook/form-submission";



// ===== UI Utility functions =====

export function hideAllStates(): void {
    /*
        Power to hide all sections on the page,
        used before showing a specific section
    */
    document.querySelectorAll("section")
        .forEach(el => el.classList.add("hidden"));
}


export function showPageState(element_id: string): void {
    /*
        Show a specific section by ID and hide all others
    */
    const element = document.getElementById(element_id);
    if (element) {
        hideAllStates();
        element.classList.remove("hidden");
    }

    if (element_id === "form-state") {
        initializeFormUI();
    }
}

export function setFormFieldValue(elementId: string, elementValue: string) {
  const formElement = document.getElementById(elementId) as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | null;
  if (formElement) {
    formElement.value = elementValue;
  }
}

export async function loadTicketDraftFormFromEditToken(editToken: string): Promise<void> {
    /*
        Load existing ticket draft data from server using the edit token,
        and populate the form fields for editing.
    */
    const webhookUrl = `${FORM_SUBMISSION_WEBHOOK_TO_BACKEND}?editToken=${encodeURIComponent(editToken)}`;
    try {
        const webhookResponse = await fetch(webhookUrl);
        // Check if the response was successful
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
        const webhookData: TicketDraftData[] = JSON.parse(responseText);
        validateTicketDraftData(webhookData);

        // Populate form fields
        const formResponse = webhookData[0];
        setFormFieldValue("ticketTitle", formResponse.ticketTitle || "");
        setFormFieldValue("ticketDescription", formResponse.ticketDescription || "");
        setFormFieldValue("ticketType", formResponse.ticketType || "");
        setFormFieldValue("ticketImpact", formResponse.ticketImpact || "");
        setFormFieldValue("assigneeTeam", formResponse.assigneeTeam || "");
        setFormFieldValue("assignee", formResponse.assignee || "");
        setFormFieldValue("userEmail", formResponse.userEmail || "");
        setFormFieldValue("aiTicketDrafterEnabled", formResponse.aiTicketDrafterEnabled || "");
        setFormFieldValue("editToken", editToken);
        setFormFieldValue("emailMessageId", formResponse.emailMessageId || "");
        // Show the form, populated with all pre-filled fields and ready for editing
        showPageState("form-state");
    } catch (err) {
        console.error(`Failed to load ticket draft data, error: ${err}`);
        throw err;
    }
}

export function initializeFormUI(): void {
    /*
        Fullscreen ticket description box handler
    */
    const textarea = document.getElementById("ticketDescription") as HTMLTextAreaElement;
    if (!textarea) return;

    let anchor: { width: string; height: string } | null = null;

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
            if (anchor) {
                textarea.style.width = anchor.width;
                textarea.style.height = anchor.height;
            }
        }

        textarea.focus();
    });
}

// Error handling and display functions for form validation

export function clearErrors(): void {
  document.querySelectorAll(".error").forEach(el => el.textContent = "");
  document.querySelectorAll("input, select, textarea")
    .forEach(el => el.classList.remove("input-error"));
}


export function showErrors(errors: any[]): void {
  if (!errors) return;

  // Normalize input so we always work with an array
  if (!Array.isArray(errors)) {
    console.error("Non-validation error:", errors);
    return;
  }

  const friendlyMessages: Record<string, string> = {
    minLength: "This field cannot be empty.",
    format: "Please enter a valid email address.",
    enum: "Please select a valid option.",
    required: "This field is required."
  };

  const shownFields = new Set<string>();

  errors.forEach(err => {
    if (!err) return;

    let field = "";

    if (typeof err.instancePath === "string") {
      field = err.instancePath.split("/").pop() || "";
    }

    if (err.keyword === "required" && err.params?.missingProperty) {
      field = err.params.missingProperty;
    }

    if (!field || shownFields.has(field)) return;
    shownFields.add(field);

    const message =
      friendlyMessages[err.keyword] ||
      err.message ||
      "Invalid input.";

    const input = document.querySelector(`[name="${field}"]`) as HTMLElement;
    const errorEl = document.querySelector(`[data-error-for="${field}"]`) as HTMLElement;

    if (input) input.classList.add("input-error");
    if (errorEl) errorEl.textContent = message;
  });
}