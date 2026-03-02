/*
 * Intercept form submission and validate with AJV.
 * If invalid → show field errors.
 * If valid → allow normal POST to n8n.
 */

import Ajv2020 from 'https://esm.sh/ajv/dist/2020.js';
import addFormats from 'https://esm.sh/ajv-formats';

const ajv = new Ajv2020({ allErrors: true });
addFormats(ajv);

const schema = {
  type: "object",
  additionalProperties: false,
  required: [
    "ticketTitle",
    "ticketDescription",
    "ticketType",
    "ticketImpact",
    "assigneeTeam",
    "assignee",
    "userEmail",
    "aiTicketDrafterEnabled"
  ],
  properties: {
    ticketTitle: { type: "string", minLength: 1 },
    ticketDescription: { type: "string", minLength: 1 },
    ticketType: { type: "string", enum: ["Bug", "Feature", "Task", "Story", "Epic"] },
    ticketImpact: { type: "string", enum: ["Major", "Urgent", "Minor", "Internal"] },
    assigneeTeam: { type: "string", enum: ["Captains of the World"] },
    assignee: { type: "string", enum: ["Edrees Saied"] },
    userEmail: { type: "string", format: "email", minLength: 1 },
    aiTicketDrafterEnabled: { type: "string", enum: ["Yes", "No"] }
  }
};

const validate = ajv.compile(schema);
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
  const rawPayload = Object.fromEntries(formData.entries());

  const allowedKeys = Object.keys(schema.properties);
  const filteredPayload = Object.fromEntries(
    Object.entries(rawPayload).filter(([key]) =>
      allowedKeys.includes(key)
    )
  );

  if (!validate(filteredPayload)) {
    e.preventDefault();
    showErrors(validate.errors);
  }
});