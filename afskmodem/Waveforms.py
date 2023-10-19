import wave
import struct
"""
    Waveforms provides functions to load waveforms from files and return them 
    as lists of amplitudes, stored as either bytes or ints.
"""

WAVEFORMS_DIR = "waveforms/"

class Waveforms:
    def __init__(self, digital_mode):
        self.digital_mode = digital_mode

    # Load waveform data from a file 
    # and convert it to a list of amplitudes as ints
    def __loadWavFile(self, filename: str) -> list[int]:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            expFrames = []
            for i in range(0, nFrames):
                sFrame = f.readframes(1)
                expFrames.append(struct.unpack("<h", sFrame)[0])
            return expFrames

    # Load waveform data from a file 
    # and convert it to a list of amplitudes as bytes
    def __loadRawWavFile(self, filename: str) -> bytes:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    # Silence (20ms) to pad output with for TX
    def getTxSilence(self) -> bytes: 
        return self.__loadRawWavFile(WAVEFORMS_DIR + "_.wav")
    
    # Space tone as bytes for transmitting
    def getTxSpace(self) -> bytes: 
        return self.__loadRawWavFile(WAVEFORMS_DIR + 
                                     self.digital_mode + "/0.wav")
    
    # Mark tone as bytes for transmitting
    def GetTxMark(self) -> bytes: 
        return self.__loadRawWavFile(WAVEFORMS_DIR + 
                                     self.digital_mode + "/1.wav")
    
    # Space tone as int array for receiving
    def getRxSpace(self) -> list[int]: 
        return self.__loadWavFile(WAVEFORMS_DIR + 
                                  self.digital_mode + "/0.wav")
    
    # Mark tone as int array for receiving
    def getRxMark(self) -> list[int]: 
        return self.__loadWavFile(WAVEFORMS_DIR + 
                                  self.digital_mode + "/1.wav")
    
    # Single training sequence cycle for RX clock recovery
    def getRxTraining(self) -> list[int]: 
        return self.getRxMark() + self.getRxSpace()