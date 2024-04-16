from afskmodem import Receiver

def main():
    receiver = Receiver(1200)
    print("AFSKmodem RX Demo")
    while(True):
        print("Waiting for message...")
        while(True):
            rxData = receiver.receive(100, True)
            if(rxData != ""):
                print("Transmission received:")
                print("")
                print(rxData)
                print("")
                print("Done. (CTRL-C to exit)")
            break

if(__name__ == "__main__"):
    try:
        main()
    except(KeyboardInterrupt):
        print("CTRL-C")
        pass