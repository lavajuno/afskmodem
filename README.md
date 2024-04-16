# afskmodem
A software-defined Audio Frequency-Shift Keying modem designed for analog FM 
radios. Uses the device's default audio input and output.

[Source code](https://github.com/lavajuno/afskmodem)

[Releases](https://github.com/lavajuno/afskmodem/releases)

# Usage Examples

### Sending a message:
```python
from afskmodem import Transmitter
t = Transmitter(1200)
t.transmit("Hello World!")

# Argument can be either str or bytes
```

### Receiving a message:
```python
from afskmodem import Receiver
r = Receiver(1200)
recv_data = r.receive(100, True)
print(recv_data)

# Set the second argument to True to decode as a UTF-8 string
```

### Constructing a Transmitter with a custom training sequence:
```python
from afskmodem import Transmitter
t = Transmitter(1200, 1.5)
```

### Constructing a Receiver with a higher sensitivity:
```python
from afskmodem import Receiver
r = Receiver(1200, 14000, 11000)
```

> Note: Although it is possible to change these parameters, the defaults usually
> perform the best.
> The input device's volume should be adjusted before changing the sensitivity
> of Receiver.

### Writing to a .wav file with Transmitter:
```python
from afskmodem import Transmitter

t = Transmitter(1200)
t.save("Héellóo World!", "afsk.wav")

# First argument can be either str or bytes
```

### Reading from a .wav file with Receiver:
```python
from afskmodem import Receiver

r = Receiver(1200)
recv_data = r.load("afsk.wav", True)
assert recv_data == "Héellóo World!"

# Set the second argument to True to decode as a UTF-8 string
```

> Note: Input files for Receiver.load() must be 48khz 16-bit mono.
> Transmitter.save() outputs files in this format.

# Supported Baud Rates
afskmodem supports common baud rates like 300, 600, 1200, 2400, 4800, and 9600.
It can use any baud rate as long as it is a factor of the sample rate (48000).

# Classes

## Receiver

Receiver is configured with a baud rate and optional audio settings,
and provides functionality for receiving and decoding messages.

### Constructor parameters

`baud_rate`: (required, int, 300-12000) Baud rate for this Receiver

`amp_start_threshold`: (optional, int, 0-32768) Amplitude to detect start of 
signal

`amp_end_threshold`: (optional, int, 0-32768) Amplitude to detect end of signal


### Member Functions

`receive(timeout: float, string: bool = False) -> bytes|str` - Listens and
decodes a message. Takes a timeout in seconds. Set `string` to True to decode
the result as a UTF-8 string.

`read(filename: str, string: bool = False) -> bytes|str` - Listens and decodes 
a message, reading input from the specified .wav file. Input file must be 48khz
16-bit mono. Set `string` to True to decode the result as a UTF-8 string.

## Transmitter

Transmitter is instantiated with a mode and optional audio settings,
and provides functionality for encoding and sending messages.

### Constructor Parameters

`baud_rate`: (required, int, 300-12000) Baud rate for this Transmitter

`training_sequence_time`: (optional, float) Length of the training sequence in 
seconds

### Member Functions

`transmit(data: str|bytes)`: Encodes and transmits a message. If given a string,
will encode it as UTF-8 before transmitting.

`write(data: str|bytes, filename: str)`: Encodes and transmits a message, saving 
the audio to a .wav file instead of playing it. If given a string, will encode
it as UTF-8 before transmitting.
