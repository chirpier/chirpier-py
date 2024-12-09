"""This module provides an example of how to use the Chirpier SDK."""

from urllib.error import HTTPError

try:
    from chirpier import ChirpierClientManager, Event
except ImportError:
    print("Error: Unable to import 'chirpier'. Make sure it's installed correctly.")
    exit(1)


def main():
    """Main function to run the example."""
    # Initialize the client
    ChirpierClientManager.initialize(api_key="your-api-key")

    # Create an event
    event = Event(
        group_id="f3438ee9-b964-48aa-b938-a803df440a3c",
        stream_name="Clicks",
        value=1
    )

    # Send the event
    try:
        ChirpierClientManager.monitor(event)
        print("Event sent successfully!")
    except (ConnectionError, HTTPError) as e:
        print(f"Failed to send event: {e}")


if __name__ == "__main__":
    main()
