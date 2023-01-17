from afskmodem import DigitalReceiver
from afskmodem import DigitalModes
receiver = DigitalReceiver(DigitalModes.default())
print("AFSKmodem RX Demo")
while(True):
    print("Waiting for message...\n")
    while(True):
        rxData, errorCount = receiver.rx()
        if(rxData != b""):
            print("Transmission received. " + str(errorCount) + " errors corrected.")
            print(rxData.decode("ascii", "ignore"))
            print("\nDone. (CTRL-C to exit)")
        break