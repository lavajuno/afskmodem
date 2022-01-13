from nbfmmodem import digitalTransmitter
from nbfmmodem import digitalModulationTypes
transmitter = digitalTransmitter(digitalModulationTypes.default())
print("NBFMmodem TX Demo")
while True:
    print("Enter message string (ASCII):")
    userMessage = input()
    print("Transmitting...")
    transmitter.tx(userMessage.encode("ascii", "ignore"))
    print("Done. (CTRL-C to exit)\n")
