# afskmodem
A python library for transmitting and receiving digital data with Audio Frequency-Shift Keying
## Classes:
### digitalModulationTypes():
#### Functions:
> afsk500(): Audio Frequency-Shift Keying at 500 baud. (RECOMMENDED IN MOST CASES)

> afsk750(): Audio Frequency-Shift Keying at 750 baud.

> afsk1000(): Audio Frequency-Shift Keying at 1000 baud.

> afsk1500(): Audio Frequency-Shift Keying at 1500 baud.

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
> dataLen: (required, int) Data length in bytes

###### Returns:
> (double) Estimated transmission time in seconds.

## Examples:
### Sending a message:
```
from afskmodem import digitalTransmitter, digitalModulationTypes
t = digitalTransmitter(digitalModulationTypes.afsk500())
t.tx("Hello World!".encode("ascii", "ignore"))
```
### Receiving a message:
```
from afskmodem import digitalReceiver, digitalModulationTypes
r = digitalReceiver(digitalModulationTypes.afsk500())
print(r.rx().decode("ascii", "ignore"))
```
