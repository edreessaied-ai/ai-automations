/*
    Contains logic for schema validation of ticket drafter form data.
*/

import Ajv2020 from 'https://esm.sh/ajv/dist/2020.js';
import addFormats from 'https://esm.sh/ajv-formats';

const ajv = new Ajv2020({ allErrors: true });
addFormats(ajv);

export class TicketDraftSchemaValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "TicketDraftSchemaValidationError";
  }
}

export const schema = {
  type: "array",
  minItems: 1,
  maxItems: 1,
  items: {
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
      aiTicketDrafterEnabled: { type: "string", enum: ["Yes", "No"] },
      
      // Optional Fields
      id: {},
      createdAt: {},
      updatedAt: {}
    },
  }
};

export const validate = ajv.compile(schema);

export function validateTicketDraftData(data) {
    const valid = validate(data);
    if (!valid) {
        throw new TicketDraftSchemaValidationError(
            "Ticket draft schema validation failed: " + JSON.stringify(validate.errors)
        );
    }
}