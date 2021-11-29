from nbfmmodem import digitalReceiver
from nbfmmodem import digitalModulationTypes
receiver = digitalReceiver(digitalModulationTypes.default())
print("NBFMmodem RX Demo")
while(True):
    print("Waiting for message...\n")
    while(True):
        rxData = receiver.rx()
        if(rxData != b""):
            print(rxData.decode("utf-8"))
            print("\nDone. (CTRL-C to exit)")
            break