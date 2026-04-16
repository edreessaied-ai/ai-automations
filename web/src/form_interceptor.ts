/*
  Intercept form submission and validate the schema.

  SPA-compatible version:
  - Mounted explicitly via mountFormInterceptor()
  - Uses router navigation instead of full page reload
  - Namespaced under /form/*
*/

import { retry_wrapper } from "./retry_util.js";
import { validateTicketDraftData } from "./ticket_schema.js";
import {
  MissingDataError,
  TicketDraftSubmissionError,
  showPageState,
  clearErrors,
} from "./ticket_drafter_util.js";
import { navigate } from "./router.js";

let isMounted = false;

export function mountFormInterceptor(): void {
  if (isMounted) return;
  isMounted = true;

  const form = document.querySelector("#form-state form") as HTMLFormElement | null;
  if (!form) {
    console.warn("mountFormInterceptor: form not found");
    return;
  }

  form.addEventListener("submit", handleSubmit);
}

async function handleSubmit(e: Event) {
  e.preventDefault();

  const form = e.currentTarget as HTMLFormElement;

  showPageState("loading-state");
  clearErrors();

  // Extract editToken from URL
  const params = new URLSearchParams(window.location.search);
  let editToken: string | undefined = params.get("editToken") ?? undefined;

  if (editToken) {
    const editTokenEl = document.querySelector("#editToken") as HTMLInputElement | null;
    if (editTokenEl) editTokenEl.value = editToken;
  }

  const formData = new FormData(form);
  const payload: Record<string, string> =
    Object.fromEntries(formData.entries()) as any;

  // Frontend validation (throws if invalid)
  validateTicketDraftData([payload as any]);

  try {
    async function submitForm() {
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

      const data = await response.json();

      if (!data?.editToken) {
        throw new MissingDataError("Missing editToken in response");
      }

      return data.editToken;
    }

    editToken = await retry_wrapper(() => submitForm(), { retries: 30 });

    // SPA navigation within /form namespace
    const query = editToken ? `?editToken=${editToken}` : "";
    navigate(`/form/submitted${query}`);

  } catch (err) {
    console.error("Form submission failed:", err);
    showPageState("state-error");
  }
}
