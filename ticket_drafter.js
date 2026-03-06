/*
    Contains the logic for the ticket drafter form.
    Handles support for creating new drafts and editing existing ones.
*/

import { 
    FRONTEND_FORM_LINK,
    hideAllStates,
    loadTicketDraftFormFromEditToken,
    showPageState,
} from "./ticket_drafter_utilities.js";


// Fetch params in the URL
const PAGE_PARAMS = new URLSearchParams(window.location.search);
// Determine which page state to show based on the "state" URL param
const PAGE_STATE = PAGE_PARAMS.get("state");
// Parse the edit token if present
const EDIT_TOKEN = PAGE_PARAMS.get("editToken");


async function mainInterface() {
    /*
        Core page manager
        Determines which section to show based on URL params and manages the flow of the application.
    */

    // Fetch params in the URL
    const pageParams = new URLSearchParams(window.location.search);
    // Determine which page state to show based on the "state" URL param
    const pageState = pageParams.get("state");
    // Parse the edit token if present
    const editToken = pageParams.get("editToken");

    // Initially hide all sections until we determine which one to show
    hideAllStates();

    // If there's no state, show the new form. 
    // If it's "submitted", show the submitted state.
    // If it's "edit", load the draft for editing.
    // Otherwise, show an error.
    if (!pageState || pageState === "form") {
        // New form
        // New form is the default state for now
        // at least until we implement a default landing page or other states.
        showPageState("form-state");
    } else if (pageState === "submitted") {
        // Submmitted state - show the submitted page with the edit link if edit token is present
        
        // Link the new form button to the fresh form page
        document.getElementById("new-form").href = FRONTEND_FORM_LINK;

        // If there's an edit token, set the edit button href to include the edit token, otherwise disable the edit link
        const editButtonElement = document.getElementById("edit-form");
        if (editButtonElement) {
            if (editToken) {
                editButtonElement.href =
                    `${FRONTEND_FORM_LINK}?state=edit&editToken=${encodeURIComponent(editToken)}`;
            } else {
                editButtonElement.classList.add("disabled");
                editButtonElement.removeAttribute("href");
            }
        }

        // Show the submission acknowledgment page
        showPageState("state-submitted");
    } else if (pageState === "edit") {
        // Show a temporary loading message
        showPageState("loading-state");
        
        // Fetch the existing ticket draft data using
        // the edit token and populate the form for editing.
        // If loading fails, show an error state.
        try {
            await loadTicketDraftFormFromEditToken(editToken);
        } catch (err) {
            showPageState("state-error");
        }
    } else {
        // Invalid state
        showPageState("unknown-state");
    }
}


mainInterface();