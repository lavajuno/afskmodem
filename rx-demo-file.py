from afskmodem import Receiver

def main():
    receiver = Receiver(1200)
    print("AFSKmodem File Read Demo")
    while(True):
        print("Enter path to file to read (ex. \"./myfile.wav\"):")
        rxData = receiver.load(input(), True)
        if(rxData == ""):
            print("Could not decode.")
        else:
            print("Transmission decoded:")
            print("")
            print(rxData)
            print("")
            print("Done. (CTRL-C to exit)")
            

if(__name__ == "__main__"):
    try:
        main()
    except(KeyboardInterrupt):
        print("CTRL-C")
        pass