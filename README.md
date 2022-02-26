# afskmodem
A python library for transmitting and receiving digital data with Audio Frequency-Shift Keying
## Classes:
### digitalModulationTypes():
#### Functions:
> afsk600(): Audio Frequency-Shift Keying at 600 baud. 

> afsk1200(): Audio Frequency-Shift Keying at 1200 baud. (RECOMMENDED IN MOST CASES)

### digitalReceiver():
#### Parameters:
> digitalModulationType: (required, digitalModulationTypes) Type of digital modulation to listen for.

> amplitudeStartThreshold: (optional, int, 0-32768) Amplitude to detect start of training block

> amplitudeEndThreshold: (optional, int, 0-32768) Amplitude to detect end of data

> amplifierDeadzone: (optional, int, 0-32768) Deadzone for amplification function

#### Functions:
##### rx():
###### Parameters:
> timeout: (int) Recording timeout in seconds.

###### Returns:
> (bytes) Received data

### digitalTransmitter():
#### Parameters:
> digitalModulationType: (required, digitalModulationTypes) Type of digital modulation to transmit.

> trainingSequenceTime: (optional, float) Length of the training sequence in seconds.

#### Functions:
##### tx():
###### Parameters:
> data: (required, bytes) Data to transmit
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
t = digitalTransmitter(digitalModulationTypes.afsk1200())
t.tx("Hello World!".encode("ascii", "ignore"))
```
### Receiving a message:
```
from afskmodem import digitalReceiver, digitalModulationTypes
r = digitalReceiver(digitalModulationTypes.afsk1200())
print(r.rx().decode("ascii", "ignore"))
```
