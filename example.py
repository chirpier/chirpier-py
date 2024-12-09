"""This module provides an example of how to use the Chirpier SDK."""

try:
    from chirpier import Chirpier, Event
except ImportError:
    print("Error: Unable to import 'chirpier'. Make sure it's installed correctly.")
    exit(1)

import time


def main():
    """Main function to run the example."""
    c = Chirpier(key="your-api-key")

    event = Event(group_id="test-group", stream_name="test-stream", value=42.0)
    c.monitor(event)

    # Wait a bit to allow processing
    time.sleep(5)


if __name__ == "__main__":
    main()
