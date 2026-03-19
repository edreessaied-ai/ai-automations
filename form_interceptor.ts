/*
    Intercept form submission and validate the schema.
    If invalid -> show errors and prevent form submission.
    If valid -> allow form submission to proceed as normal.
 */

import { retry_wrapper } from "./retry_util.js";
import { TicketDraftData, validateTicketDraftData } from "./ticket_schema.js";
import {
  FRONTEND_FORM_LINK,
  MissingDataError,
  TicketDraftSubmissionError,
  showPageState,
  clearErrors,
  showErrors 
} from "./ticket_drafter_util.js";

const form = document.querySelector("form") as HTMLFormElement;

form.addEventListener("submit", async (e: Event) => {
    // Prevent default form submission behavior to allow for validation and custom handling
    // If validation succeeds, we will manually submit the form after validation. If it fails, we will show errors and not submit.
    // This is done to provide a better user experience by not submitting the form until we are sure the data is valid.
  e.preventDefault();

  showPageState("loading-state");
  clearErrors();

  // Get the edit token from the URL if it exists
  const params = new URLSearchParams(window.location.search);

  // If there's an edit token, set it in the form so the backend knows this is an edit request
  let editToken: string | undefined = params.get("editToken") ?? undefined;
  if (editToken) {
    const editTokenEl = document.querySelector("#editToken") as HTMLInputElement;
    if (editTokenEl) editTokenEl.value = editToken;
  }

  const formData = new FormData(form);
  const payload: Record<string, string> =
    Object.fromEntries(formData.entries()) as any;

  // Frontend validation
  validateTicketDraftData([payload as any]);

  // Submit the form data to the backend and handle errors
  try {
    async function submitForm(): Promise<string> {
      const response = await fetch(form.action, {
        method: form.method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new TicketDraftSubmissionError(
          `Form submission failed with status ${response.status}: ${response.statusText}`
        );
      }

      // Extract edit token from the response
      const rawResponseData = await response.text();
      const formResponseArray: TicketDraftData[] = JSON.parse(rawResponseData);
      let formResponseData: TicketDraftData = formResponseArray[0];
      if (!formResponseData?.editToken) {
        throw new MissingDataError("Missing editToken in response");
      }
      return formResponseData.editToken;
    }
    editToken = await retry_wrapper(() => submitForm(), { retries: 60 });
  } catch (err: any) {
    console.error("Form submission failed:", err);
    showPageState("state-error");
  }

  // If submission is successful, redirect to the submitted page with the edit token
  const redirectToSubmittedPageURL = new URL(FRONTEND_FORM_LINK);
  redirectToSubmittedPageURL.searchParams.set("state", "submitted");
  if (editToken) {
    redirectToSubmittedPageURL.searchParams.set("editToken", editToken);
  }
  window.location.href = redirectToSubmittedPageURL.toString();
});