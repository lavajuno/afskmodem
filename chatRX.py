from nbfmmodem import digitalReceiver
from nbfmmodem import digitalModulationTypes
receiver = digitalReceiver(digitalModulationTypes.default())
print("NBFMmodem chatRX Demo")
print("Listener started on default audio device. Press CTRL-C to exit.\n")
while(True):
    while(True):
        rxData = receiver.rx()
        if(rxData != b""):
            print(rxData.decode("utf-8"))
            break