from afskmodem import DigitalReceiver
receiver = DigitalReceiver(1200)
print("AFSKmodem RX Demo")
while(True):
    print("Waiting for message...\n")
    while(True):
        rxData = receiver.rx(100)
        if(rxData != b""):
            print("Transmission received.")
            print(rxData.decode("utf-8", "ignore"))
            print("\nDone. (CTRL-C to exit)")
        break