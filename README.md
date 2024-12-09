# Chirpier SDK

Chirpier SDK is a Python SDK that simplifies event tracking and monitoring in your Python applications. It provides an easy-to-use API for sending, managing, and analyzing events, making it ideal for developers building data-driven applications.

## Features

- **Event Management**: Easily create and track events in your system.
- **Error Handling**: Comprehensive error management for reliable tracking.
- **Lightweight**: Minimal dependencies for faster integration.
- **Scalable**: Designed for both small applications and enterprise-level workloads.

## Installation

Install Chirpier SDK using pip:

```bash
pip install chirpier-py
```

## Usage

Here’s a quick example of how to use Chirpier SDK:

```python
from chirpier import Chirpier, Event

# Initialize the client
Chirpier.initialize(api_key="your-api-key")

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

## Components

### **Client**

- Initializes the connection with the event tracking service.
- Provides methods for sending and managing events.

### **Event**

- Represents an event with properties like `group_id`, `stream_name`, and `value`.

### **Utils**

- Helper functions for advanced use cases.

### **Error Handling**

- Custom exceptions to handle and debug errors effectively.

## Testing

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

If you have any questions or need support, please open an issue on the GitHub repository or contact us at contact@chirpier.co.

## API Reference

### Client

```python
Chirpier.initialize(api_key="your-api-key")
```

#### Parameters

- `your-api-key` (str): Your Chirpier API key

### Event

```python
event = Event(
    group_id="bfd9299d-817a-452f-bc53-6e154f2281fc",
    stream_name="My measurement",
    value=1
)
```

#### Parameters

- `group_id` (str): UUID of the monitoring group
- `stream_name` (str): Name of the measurement stream
- `value` (float): Numeric value to record

### Monitor

```python
Chirpier.monitor(event)
```

---

Start tracking your events seamlessly with Chirpier SDK!