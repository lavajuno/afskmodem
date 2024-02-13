# afskmodem
A software-defined Audio Frequency-Shift Keying modem designed for analog FM radios. Uses the device's default audio input and output.

[Source code](https://github.com/lavajuno/afskmodem)

[Releases](https://github.com/lavajuno/afskmodem/releases)

# Usage example

### Sending a message:
```python
from afskmodem import Transmitter
t = DigitalTransmitter(1200)
t.transmit("Hello World!".encode("ascii", "ignore"))
```

### Receiving a message:
```python
from afskmodem import Receiver
r = Receiver(1200)
recv_data = r.receive(100)
print(recv_data.decode("ascii", "ignore"))
```

# Classes

## `Receiver`

Receiver is configured with a baud rate and optional audio settings,
and provides functionality for receiving and decoding messages.

### Constructor parameters

`baud_rate`: (required, int, 300-12000) Baud rate for this Receiver

`amp_start_threshold`: (optional, int, 0-32768) Amplitude to detect start of signal

`amp_end_threshold`: (optional, int, 0-32768) Amplitude to detect end of signal


### Member Functions

`receive(timeout: float) -> bytes` - Listens and decodes a message. Takes a timeout in seconds.

## `DigitalTransmitter`

DigitalTransmitter is instantiated with a mode and optional audio settings,
and provides functionality for encoding and sending messages.

### Constructor Parameters

`baud_rate`: (required, int, 300-12000) Baud rate for this Transmitter

`training_sequence_time`: (optional, float) Length of the training sequence in seconds.

### Member Functions

`transmit(data: bytes)`: Encodes and transmits a message
