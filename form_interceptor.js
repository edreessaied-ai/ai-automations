/*
    Intercept form submission and validate the schema.
    If invalid -> show errors and prevent form submission.
    If valid -> allow form submission to proceed as normal.
 */

import { validateTicketDraftData } from "./ticket_schema.js";
import { showPageState, clearErrors, showErrors } from "./ticket_drafter_utilities.js";

const form = document.querySelector("form");

form.addEventListener("submit", (e) => {
  showPageState("loading-state");
  clearErrors();

  const params = new URLSearchParams(window.location.search);
  const editToken = params.get("editToken");

  if (editToken) {
    document.querySelector("#editToken").value = editToken;
  }
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  // Validate against AJV schema and show errors if invalid.
  // If valid, allow form submission to proceed as normal.
  try {
    validateTicketDraftData([payload]);
  } catch (err) {
    showErrors(err.errors);
    e.preventDefault();
    showPageState("state-error"); 
  }
});