# AFSKmodem
A software-defined Audio Frequency-Shift Keying modem designed for analog FM radios. Uses the device's default audio input and output.

[Source code](https://github.com/lavajuno/afskmodem)

[Releases](https://github.com/lavajuno/afskmodem/releases)

# Usage example

### Sending a message:
```
from afskmodem import DigitalTransmitter, DigitalModes
t = DigitalTransmitter(DigitalModes.afsk1200())
t.tx("Hello World!".encode("ascii", "ignore"))
```

### Receiving a message:
```
from afskmodem import DigitalReceiver, DigitalModes
r = DigitalReceiver(DigitalModes.afsk1200())
recv_data, n_errors = r.rx()
print(recv_data.decode("ascii", "ignore"))
```

# Classes
## DigitalModes
DigitalModes represents the different speeds at which AFSKmodem can run.
### Member Functions
`afsk300()`: Audio Frequency-Shift Keying at 300 baud.

`afsk600()`: Audio Frequency-Shift Keying at 600 baud.

`afsk1200()`: Audio Frequency-Shift Keying at 1200 baud. (Recommended)

`afsk2400()`: Audio Frequency-Shift Keying at 2400 baud.

`afsk6000()`: Audio Frequency-Shift Keying at 6000 baud.

## `DigitalReceiver`
DigitalReceiver is configured with a mode and optional audio settings,
and provides functionality for receiving and decoding messages.
### Constructor parameters
`digital_mode`: (required, DigitalModes) Type of digital modulation to listen for.

`amp_start_threshold`: (optional, int, 0-32768) Amplitude to detect start of training block

`amp_end_threshold`: (optional, int, 0-32768) Amplitude to detect end of data


### Member Functions
`rx(timeout: int) -> bytes` - Listens and decodes a message. Takes a timeout in seconds.

## `DigitalTransmitter`
DigitalTransmitter is instantiated with a mode and optional audio settings,
and provides functionality for encoding and sending messages.
### Constructor Parameters
`digital_mode`: (required, DigitalModes) Type of digital modulation to transmit.

`training_sequence_time`: (optional, float) Length of the training sequence in seconds.

### Member Functions
`tx(data: bytes)`: Encodes and transmits a message

`estimateTxTime(data_length: int) -> float`: Estimates time to transmit a message with a given length (in bytes).
