/*
    Intercept form submission and validate the schema.
    If invalid -> show errors and prevent form submission.
    If valid -> allow form submission to proceed as normal.
 */

import { validateTicketDraftData } from "./ticket_schema.js";
import { showPageState, clearErrors, showErrors } from "./ticket_drafter_util.js";

const form = document.querySelector("form") as HTMLFormElement;

form.addEventListener("submit", (e: Event) => {
  showPageState("loading-state");
  clearErrors();

  const params = new URLSearchParams(window.location.search);
  const editToken = params.get("editToken");

  if (editToken) {
    const editTokenEl = document.querySelector("#editToken") as HTMLInputElement;
    if (editTokenEl) editTokenEl.value = editToken;
  }
  const formData = new FormData(form);
  const payload: Record<string, string> = Object.fromEntries(formData.entries()) as any;

  // Validate against AJV schema and show errors if invalid.
  // If valid, allow form submission to proceed as normal.
  try {
    validateTicketDraftData([payload as any]);
  } catch (err) {
    console.error("Form validation failed: ", err);
    showErrors((err as any).errors || [err]);
    e.preventDefault();
    showPageState("state-error");
  }
});