from afskmodem import DigitalTransmitter
from afskmodem import DigitalModulationTypes
transmitter = DigitalTransmitter(DigitalModulationTypes.default())
print("AFSKmodem TX Demo")
while True:
    print("Enter message string (ASCII):")
    userMessage = input()
    print("Transmitting...")
    transmitter.tx(userMessage.encode("ascii", "ignore"))
    print("Done. (CTRL-C to exit)\n")
