/*
    * Ticket Drafter Utilities
    Contains utility functions and error classes for the ticket drafter application.
*/


export class TicketDraftError extends Error {
  constructor(message) {
    super(message);
    this.name = "TicketDraftError";
  }
}
