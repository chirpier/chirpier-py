# Chirpier SDK

The Chirpier SDK for Python is a simple, lightweight, and efficient SDK to emit event data to Chirpier direct from your Python applications.

## Features

- Easy-to-use API for sending events to Chirpier
- Automatic batching of events for improved performance
- Automatic retry mechanism with exponential backoff
- Thread-safe operations
- Periodic flushing of the event queue

## Installation

Install Chirpier SDK using pip:

```bash
pip install chirpier
```

## Getting Started

To start using the SDK, you need to initialize it with your API key.

Here’s a quick example of how to use Chirpier SDK:

```python
from chirpier import Chirpier, Event

# Initialize the client
Chirpier.initialize(api_key="your-api-key", region="us-west")

# Monitor the event
try:
   Chirpier.monitor(Event(
      group_id="bfd9299d-817a-452f-bc53-6e154f2281fc",
      stream_name="My measurement",
      value=1
   ))
except (ConnectionError, HTTPError) as e:
   print(f"Failed to send event: {e}")
```

## API Reference

### Initialize

Initialize the Chirpier client with your API key and region. Find your API key in the Chirpier Integration page.

```python
Chirpier.initialize(api_key="your-api-key", region="us-west")
```

- `your-api-key` (str): Your Chirpier integration key
- `region` (str): Your local region - options are `us-west`, `eu-west`, `asia-southeast`

### Event

All events emitted to Chirpier must have the following properties:

```python
event = Event(
    group_id="bfd9299d-817a-452f-bc53-6e154f2281fc",
    stream_name="My measurement",
    value=1
)
```

- `group_id` (str): UUID of the monitoring group
- `stream_name` (str): Name of the measurement stream
- `value` (float): Numeric value to record

### Monitor

Send an event to Chirpier using the `monitor` function.

```python
Chirpier.monitor(event)
```

## Test

Run the test suite to ensure everything works as expected:

```bash
pytest tests/
```

## Contributing

We welcome contributions! To contribute:

1. Fork this repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a clear explanation of your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

If you have any questions or need support, please open an issue on the GitHub repository or contact us at <contact@chirpier.co>.

---

Start tracking your events seamlessly with Chirpier SDK!
