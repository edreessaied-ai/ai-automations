/*
 * Intercept form submission and validate the schema.
 * If invalid -> show errors and prevent form submission.
 * If valid -> allow form submission to proceed as normal.
 */

import { validateTicketDraftData } from "./ticket_schema.js";
import { showPageState } from "./ticket_drafter.js";

const form = document.querySelector("form");

function clearErrors() {
  document.querySelectorAll(".error").forEach(el => el.textContent = "");
  document.querySelectorAll("input, select, textarea")
    .forEach(el => el.classList.remove("input-error"));
}

function showErrors(errors) {
  const friendlyMessages = {
    minLength: "This field cannot be empty.",
    format: "Please enter a valid email address.",
    enum: "Please select a valid option.",
    required: "This field is required."
  };

  errors.forEach(err => {
    let field = err.instancePath.replace("/", "");

    // Handle required errors (instancePath is empty)
    if (err.keyword === "required") {
      field = err.params.missingProperty;
    }

    const message = friendlyMessages[err.keyword] || err.message;

    const input = document.querySelector(`[name="${field}"]`);
    const errorEl = document.querySelector(`[data-error-for="${field}"]`);

    if (input) input.classList.add("input-error");
    if (errorEl) errorEl.textContent = message;
  });
}

form.addEventListener("submit", (e) => {
  clearErrors();

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  // Validate against AJV schema and show errors if invalid.
  // If valid, allow form submission to proceed as normal.
  try {
    validateTicketDraftData(payload);
  } catch (err) {
    console.error("Form validation failed: ", err);
    e.preventDefault();
    showPageState("state-error"); 
  }
});