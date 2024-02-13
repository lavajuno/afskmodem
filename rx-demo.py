from afskmodem import DigitalReceiver
receiver = DigitalReceiver(1200)
print("AFSKmodem RX Demo")
while(True):
    print("Waiting for message...\n")
    while(True):
        rxData = receiver.rx()
        if(rxData != b""):
            print("Transmission received.")
            print(rxData.decode("ascii", "ignore"))
            print("\nDone. (CTRL-C to exit)")
        break