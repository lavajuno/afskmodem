from nbfmmodem import digitalTransmitter
from nbfmmodem import digitalModulationTypes
transmitter = digitalTransmitter(digitalModulationTypes.bpsk1000())
txString = """
The quick brown fox jumped over the lazy dog.
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
01234567890
!@#$%^&*()_+-={}[]:";'<>,.?/`~
"""
print("NBFMmodem TX Tester")
print("Transmitting... Est TX time " + str(transmitter.estTxTime(len(txString))) + " seconds.")
transmitter.tx(txString)
print("Done. (CTRL-C to exit)\n")
