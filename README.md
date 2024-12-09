# Chirpier SDK for Python

The Chirpier SDK for Python provides a simple and efficient way to integrate Chirpier's event tracking functionality into your Python applications.

## Features

- Easy-to-use API for sending events to Chirpier
- Batch processing of events for improved performance
- Automatic retry mechanism with exponential backoff
- Thread-safe operations
- Background processing of the event queue

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/chirpier/chirpier-python.git
   cd chirpier-python
   ```

2. (Optional) Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Here's a quick example of how to use the Chirpier SDK:

```python
from chirpier import Chirpier, Event
import time

def main():
    c = Chirpier(key="your-api-key")
    c.start_batch_processor()
