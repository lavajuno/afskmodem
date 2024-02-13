from afskmodem import DigitalTransmitter
transmitter = DigitalTransmitter(1200)
print("AFSKmodem TX Demo")
while True:
    print("Enter message string (ASCII):")
    userMessage = input()
    print("Transmitting...")
    transmitter.tx(userMessage.encode("ascii", "ignore"))
    print("Done. (CTRL-C to exit)\n")
