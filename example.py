"""This module provides an example of how to use the Chirpier SDK."""

from urllib.error import HTTPError
import time
try:
    from chirpier import Chirpier, Event
except ImportError:
    print("Error: Unable to import 'chirpier'. Make sure it's installed correctly.")
    exit(1)


def main():
    """Main function to run the example."""
    # Initialize the client
    Chirpier.initialize(api_key="your-api-key", region="us-west")

    # Send the event
    try:
        Chirpier.monitor(Event(
            group_id="bfd9299d-817a-452f-bc53-6e154f2281fc",
            stream_name="My measurement",
            value=1
        ))
        print("Event sent successfully!")
    except (ConnectionError, HTTPError) as e:
        print(f"Failed to send event: {e}")

    # Wait
    time.sleep(1)


if __name__ == "__main__":
    main()
