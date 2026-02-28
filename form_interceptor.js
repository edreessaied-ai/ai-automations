/*
 * Intercept form submission, validate with AJV, and send JSON payload.
 */

import Ajv from "https://cdn.jsdelivr.net/npm/ajv@8/dist/ajv.min.js";

// JSON schema for form validation
const schema = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  title: "Ticket Submission Form",
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

const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile(schema);

const form = document.querySelector("form");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Get raw form data
  const formData = new FormData(form);
  const rawPayload = Object.fromEntries(formData.entries());

  // Filter to only schema-defined fields
  const allowedKeys = Object.keys(schema.properties);
  const filteredPayload = Object.fromEntries(
    Object.entries(rawPayload).filter(([key]) => allowedKeys.includes(key))
  );

  // Validate raw payload
  if (!validate(filteredPayload)) {
    console.error("Form payload does not comply with schema:", validate.errors);
    return;
  }

  // Convert aiTicketDrafterEnabled to boolean after validation
  const payload = {
    ...filteredPayload,
    aiTicketDrafterEnabled: filteredPayload.aiTicketDrafterEnabled === "Yes"
  };

  // Submit payload via fetch
  try {
    const res = await fetch(form.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    console.log("Form submitted successfully!");
  } catch (err) {
    console.error("Failed to submit form:", err);
  }
});