"""
    This module contains tests for the Ticket Agent,
    which is responsible for generating, improving,
    and editing support tickets based on user input and instructions.
"""

from agents.ticket_agent import (
    generate_ticket,
    improve_ticket,
    edit_ticket
)
from utilities.logger import get_hourly_logger, pretty_print_json


def test_ticket_agent():
    """Test the ticket agent with a sample input and instructions."""
    INPUT_CONTENT = """
    The app crashes when I try to upload a profile picture.
    It shows an error message that says "Upload failed".
    I'm using the latest version of the app on my iPhone 12 with iOS 14.
    Please fix this ASAP!
    """
    ticket_agent_logger = get_hourly_logger(
        "ticket_agent_tests",
        write_to_console=True
    )
    ticket_agent_logger.info("Starting ticket agent tests...")
    # Generate ticket
    ticket_agent_logger.info("Generating ticket with content...")
    ticket = generate_ticket(INPUT_CONTENT)
    ticket_agent_logger.info("Generated ticket content: ")
    ticket_agent_logger.info(pretty_print_json(ticket))
    # Improve ticket
    ticket_agent_logger.info("Improving ticket...")
    improved_ticket_content = improve_ticket(ticket)
    ticket_agent_logger.info("Improved ticket content: ")
    ticket_agent_logger.info(pretty_print_json(improved_ticket_content))
    # Edit ticket
    ticket_agent_logger.info("Editing ticket...")
    edited_ticket_content = edit_ticket(
        improved_ticket_content,
        "lower priority to medium and mention mobile users"
    )
    ticket_agent_logger.info("Edited ticket content: ")
    ticket_agent_logger.info(pretty_print_json(edited_ticket_content))
    ticket_agent_logger.info("Tests complete.")
