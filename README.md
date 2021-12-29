# nbfmmodem
A python library for transmitting and receiving digital data over NBFM radio.
## Classes:
### digitalModulationTypes():
#### Functions:
> bfsk500(): Binary Frequency-Shift Keying at 500 baud. (RECOMMENDED IN MOST CASES)

> bfsk1000(): Binary Frequency-Shift Keying at 1000 baud.

> bpsk500(): Binary Phase-Shift Keying at 500 baud.

> bpsk1000(): Binary Phase-Shift Keying at 1000 baud.

### digitalReceiver():
#### Parameters:
> digitalModulationType: (required, digitalModulationTypes) Type of digital modulation to listen for.

> amplitudeStartThreshold: (optional, int, 0-32768) Amplitude to detect start of training block

> amplitudeEndThreshold: (optional, int, 0-32768) Amplitude to detect end of data

> recordingStartThreshold: (optional, int, 0-32768) Amplitude to start auto-recording

> recordingEndThreshold: (optional, int, 0-32768) Amplitude to stop auto-recording

> amplifierDeadzone: (optional, int, 0-32768) Deadzone for amplification function

#### Functions:
##### rx():
###### Parameters:
> timeout: (int) Recording timeout in seconds.

###### Returns:
> (bytes) Received data

##### rxFromWav():
###### Parameters:
> filename: (required, string) Input filename

###### Returns:
> (bytes) Received data

### digitalTransmitter():
#### Parameters:
> digitalModulationType: (required, digitalModulationTypes) Type of digital modulation to transmit.

> trainingSequenceOscillations: (optional, int) Number of oscillations of the training sequence

#### Functions:
##### tx():
###### Parameters:
> data: (required, bytes) Data to transmit
###### Returns:
> None
##### txToWav():
###### Parameters:
> data: (required, bytes) Data to transmit

> filename: (required, string) Output filename

###### Returns:
> None

##### estTxTime():
###### Parameters:
> dataLengthBytes: (required, int) Data length in bytes

###### Returns:
> (int) Estimated transmission time in seconds.

## Examples:
### Sending a message:
```
from nbfmmodem import digitalReceiver, digitalModulationTypes
t = digitalTransmitter(digitalModulationTypes.bfsk500())
t.tx("Hello World!".encode("utf-8"))
```
### Receiving a message:
```
from nbfmmodem import digitalReceiver, digitalModulationTypes
r = digitalReceiver(digitalModulationTypes.bfsk500())
print(r.rx().decode("utf-8"))
```
