from nbfmmodem import digitalTransmitter
from nbfmmodem import digitalModulationTypes
from datetime import datetime

def getDateAndTime(): # Full time and date
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

transmitter = digitalTransmitter(digitalModulationTypes.default())
print("NBFMmodem chatTX demo")
print("Enter chat nickname/callsign:")
callsign = str(input())
while True:
    print("Enter message string (ASCII):")
    userMessage = getDateAndTime() + " [" + callsign + "] "
    userMessage += input()
    print("Transmitting... Est TX time " + str(transmitter.estTxTime(len(userMessage))) + " seconds.")
    transmitter.tx(userMessage.encode("utf-8"))
    print("Done. (CTRL-C to exit)\n")
