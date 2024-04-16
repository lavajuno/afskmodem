from afskmodem import Transmitter

def main():
    transmitter = Transmitter(1200)
    print("AFSKmodem TX Demo")
    while True:
        print("Enter message string (ASCII):")
        userMessage = input()
        print("Transmitting...")
        transmitter.transmit(userMessage)
        print("Done. (CTRL-C to exit)")
        print("")

if(__name__ == "__main__"):
    try:
        main()
    except(KeyboardInterrupt):
        print("CTRL-C")
        pass