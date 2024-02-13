from afskmodem import Transmitter
transmitter = Transmitter(1200)
print("AFSKmodem TX Demo")
while True:
    print("Enter message string (ASCII):")
    userMessage = input()
    print("Transmitting...")
    transmitter.transmit(userMessage.encode("ascii", "ignore"))
    print("Done. (CTRL-C to exit)\n")
