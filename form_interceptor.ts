/*
    Intercept form submission and validate the schema.
    If invalid -> show errors and prevent form submission.
    If valid -> allow form submission to proceed as normal.
 */

import { validateTicketDraftData } from "./ticket_schema.js";
import { showPageState, clearErrors, showErrors } from "./ticket_drafter_util.js";

const form = document.querySelector("form") as HTMLFormElement;

form.addEventListener("submit", async (e: Event) => {
    // Prevent default form submission behavior to allow for validation and custom handling
    // If validation succeeds, we will manually submit the form after validation. If it fails, we will show errors and not submit.
    // This is done to provide a better user experience by not submitting the form until we are sure the data is valid.
  e.preventDefault();

  showPageState("loading-state");
  clearErrors();

  try {
    const params = new URLSearchParams(window.location.search);
    const editToken = params.get("editToken");

    if (editToken) {
      const editTokenEl = document.querySelector("#editToken") as HTMLInputElement;
      if (editTokenEl) editTokenEl.value = editToken;
    }

    const formData = new FormData(form);
    const payload: Record<string, string> =
      Object.fromEntries(formData.entries()) as any;

    // Frontend validation
    validateTicketDraftData([payload as any]);

    // Submit to backend
    const response = await fetch(form.action, {
      method: form.method || "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.message || "Server error");
    }

    const result = await response.json();

    // Handle success state
    console.log("Submission success:", result);
    showPageState("state-success");

  } catch (err: any) {
    console.error("Form submission failed:", err);
    showErrors(err);
    showPageState("state-error");
  }
});