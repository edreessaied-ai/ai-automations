/*
    Contains logic for schema validation of ticket drafter form data.
*/

// @ts-ignore
import Ajv2020 from 'https://esm.sh/ajv/dist/2020.js';
// @ts-ignore
import addFormats from 'https://esm.sh/ajv-formats';

const ajv = new Ajv2020({ allErrors: true });
addFormats(ajv);

export class TicketDraftSchemaValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TicketDraftSchemaValidationError";
  }
}

interface TicketDraftData {
  ticketTitle: string;
  ticketDescription: string;
  ticketType: "Bug" | "Feature" | "Task" | "Story" | "Epic";
  ticketImpact: "Major" | "Urgent" | "Minor" | "Internal";
  assigneeTeam: "Captains of the World";
  assignee: "Edrees Saied";
  userEmail: string;
  aiTicketDrafterEnabled: "Yes" | "No";
  id?: any;
  createdAt?: any;
  updatedAt?: any;
  editToken?: string;
  emailMessageId?: string;
}

export type { TicketDraftData };

const schema = {
  type: "array" as const,
  minItems: 1,
  maxItems: 1,
  items: {
    type: "object" as const,
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
      ticketTitle: { type: "string" as const, minLength: 1 },
      ticketDescription: { type: "string" as const, minLength: 1 },
      ticketType: { type: "string" as const, enum: ["Bug", "Feature", "Task", "Story", "Epic"] },
      ticketImpact: { type: "string" as const, enum: ["Major", "Urgent", "Minor", "Internal"] },
      assigneeTeam: { type: "string" as const, enum: ["Captains of the World"] },
      assignee: { type: "string" as const, enum: ["Edrees Saied"] },
      userEmail: { type: "string" as const, format: "email" as const, minLength: 1 },
      aiTicketDrafterEnabled: { type: "string" as const, enum: ["Yes", "No"] },

      // Optional Fields
      id: {},
      createdAt: {},
      updatedAt: {},
      editToken: {},
      emailMessageId: {},
    },
  }
};

const validate = ajv.compile(schema);

export function validateTicketDraftData(data: TicketDraftData[]): void {
    const valid = validate(data);
    if (!valid) {
        throw new TicketDraftSchemaValidationError(
            "Ticket draft schema validation failed: " + JSON.stringify(validate.errors)
        );
    }
}