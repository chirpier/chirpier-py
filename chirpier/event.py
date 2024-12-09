"""This module provides an event class for the Chirpier SDK."""

import uuid


class Event:
    """
    Represents an event to be monitored and sent to the Chirpier API.

    Attributes:
        group_id (str): The unique identifier for the group this event belongs to.
        stream_name (str): The name of the stream this event is part of.
        value (any): The value of the event.
    """

    def __init__(self, group_id, stream_name, value):
        """
        Initializes an Event instance.

        Args:
            group_id (str): The unique identifier for the group this event belongs to.
            stream_name (str): The name of the stream this event is part of.
            value (any): The value of the event.
        """
        self.group_id = group_id
        self.stream_name = stream_name
        self.value = value

    def is_valid(self):
        """
        Checks if the event is valid.

        Returns:
            bool: True if the event is valid, False otherwise.
        """
        try:
            uuid.UUID(self.group_id)
        except ValueError:
            return False
        return bool(self.group_id.strip()) and bool(self.stream_name.strip())

    def to_dict(self):
        """
        Converts the event to a dictionary representation.

        Returns:
            dict: A dictionary containing the event's attributes.
        """
        return {
            "group_id": self.group_id,
            "stream_name": self.stream_name,
            "value": self.value
        }
