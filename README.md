# nbfmmodem
A python library for transmitting and receiving digital data over NBFM radio.
## Classes:
### digitalModulationTypes():
#### Functions:
> bpsk500(): Binary Pulse-Shift Keying at 500 baud.

> bpsk1000(): Binary Pulse-Shift Keying at 1000 baud.

> bfsk500(): Binary Frequency-Shift Keying at 500 baud.

> bfsk1000(): Binary Frequency-Shift Keying at 1000 baud.
### digitalReceiver():
#### Parameters:
> digitalModulationType: (digitalModulationType) Type of digital modulation to listen for.

> amplitudeStartThreshold: (int) Amplitude to detect start of training block

> amplitudeEndThreshold: (int) Amplitude to detect end of data

> recordingStartThreshold: (int) Amplitude to start auto-recording

> recordingEndThreshold: (int) Amplitude to stop auto-recording

> amplifierDeadzone: (int) Deadzone for amplification function

> inputFramesPerBlock: (int) Input buffer size
#### Functions:
##### rx():
###### Parameters:
> timeout: (int) Recording timeout in seconds.
###### Returns:
> (bytes) Received data
##### rxFromWav():
###### Parameters:
> filename: (string) Input filename
###### Returns:
> (bytes) Received data
### digitalTransmitter():
#### Parameters:
> digitalModulationType: (digitalModulationType) Type of digital modulation to transmit.

> trainingSequenceOscillations: (int) Number of oscillations of the training sequence
#### Functions:
##### tx():
###### Parameters:
> data: (bytes) Data to transmit
###### Returns:
> None
##### txToWav():
###### Parameters:
> data: (bytes) Data to transmit

> filename: (string) Output filename
###### Returns:
> None
##### estTxTime():
###### Parameters:
> dataLengthBytes: (int) Data length in bytes
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
