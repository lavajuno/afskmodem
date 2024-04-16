from afskmodem import Transmitter

def main():
    transmitter = Transmitter(1200)
    print("AFSKmodem File Write Demo")
    while True:
        print("Enter message string (ASCII):")
        userMessage = input()
        print("Enter path to save file at (ex. \"./myfile.wav\"):")
        filename = input()
        print("Saving to file...")
        transmitter.write(userMessage.encode("ascii", "ignore"), filename)
        print("Done. (CTRL-C to exit)")
        print("")

if(__name__ == "__main__"):
    try:
        main()
    except(KeyboardInterrupt):
        print("CTRL-C")
        pass