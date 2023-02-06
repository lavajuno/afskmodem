# afskmodem
A software-defined Audio Frequency-Shift Keying modem designed for analog FM radios. Uses the device's default audio input and output.
## Classes:
### DigitalModes:
#### Functions:
> afsk300(): Audio Frequency-Shift Keying at 300 baud.

> afsk600(): Audio Frequency-Shift Keying at 600 baud.

> afsk1200(): Audio Frequency-Shift Keying at 1200 baud. (RECOMMENDED IN MOST CASES)

> afsk2400(): Audio Frequency-Shift Keying at 1200 baud.

> afsk6000(): Audio Frequency-Shift Keying at 6000 baud.

### DigitalReceiver():
#### Parameters:
> digital_mode: (required, DigitalModes) Type of digital modulation to listen for.

> amp_start_threshold: (optional, int, 0-32768) Amplitude to detect start of training block

> amp_end_threshold: (optional, int, 0-32768) Amplitude to detect end of data

> amp_deadzone: (optional, int, 0-32768) Deadzone for amplification function

#### Functions:
##### rx():
###### Parameters:
> timeout: (int) Recording timeout in seconds.

###### Returns:
> (bytes) Received data

### digitalTransmitter():
#### Parameters:
> digital_mode: (required, DigitalModes) Type of digital modulation to transmit.

> training_sequence_time: (optional, float) Length of the training sequence in seconds.

#### Functions:
##### tx():
###### Parameters:
> data: (required, bytes) Data to transmit
###### Returns:
> None

##### est_tx_time():
###### Parameters:
> data_length: (required, int) Data length in bytes

###### Returns:
> (double) Estimated transmission time in seconds.

## Examples:
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
print(r.rx().decode("ascii", "ignore"))
```
