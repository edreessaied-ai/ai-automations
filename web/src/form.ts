/*
  Handles all behavior for the Jira Ticket Drafter form.

  Responsibilities:
  - Attach event listeners
  - Handle textarea auto-resize
  - Clear validation errors
  - Future-proof hook for AI enhancements
*/

function getEl<T extends HTMLElement>(id: string): T | null {
  return document.getElementById(id) as T | null;
}

/* =========================
   MAIN MOUNT FUNCTION
========================= */

let isMounted = false;

export function mountForm(): void {
  if (isMounted) return;
  isMounted = true;

  const textarea = getEl<HTMLTextAreaElement>("ticketDescription");
  if (!textarea) {
    console.warn("mountForm: textarea not found");
    return;
  }

  attachTextareaAutoResize(textarea);
  attachBasicValidationHooks();
}

/* =========================
   TEXTAREA AUTO RESIZE
========================= */

const MAX_HEIGHT = 420;

function attachTextareaAutoResize(textarea: HTMLTextAreaElement): void {
  textarea.style.transition = "height 0.12s ease";

  const resize = () => {
    textarea.style.height = "auto";

    const newHeight = Math.min(textarea.scrollHeight, MAX_HEIGHT);
    textarea.style.height = `${newHeight}px`;

    textarea.style.overflowY =
      textarea.scrollHeight > MAX_HEIGHT ? "auto" : "hidden";
  };

  textarea.addEventListener("input", resize);
  textarea.addEventListener("focus", resize);

  // initial sizing
  resize();
}

/* =========================
   VALIDATION HOOKS (LIGHTWEIGHT)
========================= */

function attachBasicValidationHooks(): void {
  const fields = [
    "ticketTitle",
    "ticketDescription",
    "ticketType",
    "ticketImpact",
    "assigneeTeam",
    "assignee",
    "userEmail",
    "aiTicketDrafterEnabled",
  ];

  fields.forEach((id) => {
    const el = getEl<HTMLInputElement | HTMLSelectElement>(id);
    if (!el) return;

    el.addEventListener("input", () => clearError(id));
    el.addEventListener("change", () => clearError(id));
  });
}

/* =========================
   ERROR HANDLING
========================= */

function clearError(fieldId: string): void {
  const errorEl = document.querySelector(
    `[data-error-for="${fieldId}"]`
  ) as HTMLElement | null;

  const input = getEl<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(
    fieldId
  );

  if (errorEl) errorEl.textContent = "";

  if (input) {
    input.classList.remove("input-error");
  }
}
