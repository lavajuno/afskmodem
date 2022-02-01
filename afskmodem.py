"""
x---------------------------------------x
| AFSKmodem - Accessible Digital Radio  |
| https://jvmeifert.github.io/afskmodem |
x---------------------------------------x
"""
from datetime import datetime
import wave
import struct
import pyaudio
import os
from time import sleep

################################################################################ PROGRAM DEFAULTS

# USER-CONFIGURABLE PARAMETERS: Although these should work fine as-is, fine-tuning them will not affect functionality.
#
# Training sequence time (in seconds)
TRAINING_SEQUENCE_TIME = 0.5
#
# Instant amplitude required to recognize the training sequence (0-32768, Default 20000)
AMPLITUDE_START_THRESHOLD = 20000
#
# Chunk amplitude at which decoding stops (0-32768, Default 15000)
AMPLITUDE_END_THRESHOLD = 15000
#
# Chunk amplitude required to start recording (0-32768, Default 20000) * SQUELCH SHOULD BE ENABLED ON RX HARDWARE
RECORDING_START_THRESHOLD = 20000
#
# Chunk amplitude required to stop recording (0-32768, Default 15000) * SQUELCH SHOULD BE ENABLED ON RX HARDWARE
RECORDING_END_THRESHOLD = 15000
#
# Amplifier function deadzone (0-32768, Default 128)
AMPLIFIER_DEADZONE = 128
#
# Frames per buffer for audio input (1024-4096, Default 2048) - Smaller blocks increase CPU usage but decrease latency
INPUT_FRAMES_PER_BLOCK = 2048

# SYSTEM PARAMETERS: DO NOT CHANGE THESE!
#
# How many samples per second we are recording (DO NOT CHANGE, sound card resamples if needed)
SAMPLE_RATE = 48000
#
# Wav format (DO NOT CHANGE, sound card handles format conversion if needed)
FORMAT = pyaudio.paInt16
#
# Input+output channels (DO NOT CHANGE, sound card handles stereo conversion if needed)
CHANNELS = 1
#
# Directory where ideal waves are stored
IDEAL_WAVES_DIR = "data/ideal_waves/"

################################################################################ LOGGING

def getDateAndTime(): # Long date and time
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

# Where to generate logfile
LOG_PATH = "afskmodem.log"
#
# Logging level (0: INFO, 1: WARN, 2: ERROR, 3: FATAL, 4: NONE)
LOG_LEVEL = 0
#
# Should the log be silent? (print to file but not to console)
LOG_SILENT = False
#
# How the log identifies which module is logging.
LOG_PREFIX = "(AFSKMODEM)"

# Instantiate log
try:
    os.remove(LOG_PATH)
except:
    if(not LOG_SILENT):
        print(getDateAndTime() + " [INFO]  " + LOG_PREFIX + " No previous log file exists. Creating one now.")

with open(LOG_PATH, "w") as f:
    f.write(getDateAndTime() + " [INFO]  " + LOG_PREFIX + " Logging initialized.\n")
    if(not LOG_SILENT):
        print(getDateAndTime() + " [INFO]  " + LOG_PREFIX + " Logging initialized.")


def log(level: int, data: str):
    if(level >= LOG_LEVEL):
        output = getDateAndTime()
        if(level == 0):
            output += " [INFO]  "
        elif(level == 1):
            output += " [WARN]  "
        elif(level == 2):
            output += " [ERROR] "
        else:
            output += " [FATAL] "
        output += LOG_PREFIX + " "
        output += data
        with open(LOG_PATH, "a") as f:
            f.write(output + "\n")
        if(not LOG_SILENT):
            print(output)

################################################################################ DIGITAL MODULATION TYPES
class digitalModulationTypes:
    def afsk600() -> str: # Audio Frequency-Shift Keying (600 baud)
        return "afsk600"
    def afsk1000() -> str: # Audio Frequency-Shift Keying (1000 baud)
        return "afsk1000"
    def afsk1200() -> str: # Audio Frequency-Shift Keying (1200 baud)
        return "afsk1200"
    def afsk1500() -> str: # Audio Frequency-Shift Keying (1500 baud)
        return "afsk1500"
    def default() -> str: # Default (AFSK1200)
        return "afsk1200"
    
    # Unit time in samples
    def getUnitTime(digitalModulationType: str) -> int:
        if(digitalModulationType == "afsk600"):
            return int(SAMPLE_RATE / 600)
        elif(digitalModulationType == "afsk1000"):
            return int(SAMPLE_RATE / 1000)
        elif(digitalModulationType == "afsk1200"):
            return int(SAMPLE_RATE / 1200)
        elif(digitalModulationType == "afsk1500"):
            return int(SAMPLE_RATE / 1500)
        else: # default
            return int(SAMPLE_RATE / 1200)

    # Training sequence oscillations for specified time
    def getTsOscillations(sequenceTime: int, digitalModulationType: str) -> int:
        if(digitalModulationType == "afsk600"):
            return int(600 * sequenceTime / 2)
        elif(digitalModulationType == "afsk1000"):
            return int(1000 * sequenceTime / 2)
        elif(digitalModulationType == "afsk1200"):
            return int(1200 * sequenceTime / 2)
        elif(digitalModulationType == "afsk1500"):
            return int(1500 * sequenceTime / 2)
        else: # default
            return int(1200 * sequenceTime / 2)

################################################################################ IDEAL WAVES
class idealWaves: # Ideal waves for TX and RX
    def __init__(self, digitalModulationType = digitalModulationTypes.default()):
        self.digitalModulationType = digitalModulationType

    # Load wav data to int array
    def __loadWavData(self, filename: str) -> list:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            expFrames = []
            for i in range(0, nFrames):
                sFrame = f.readframes(1)
                expFrames.append(struct.unpack("<h", sFrame)[0])
            return expFrames

    # Load wav data to bytes
    def __loadRawWavData(self, filename: str) -> bytes:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    def getTxSilence(self) -> bytes: # Silence (20ms) to pad output with for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + "_.wav")
    def getTxSpace(self) -> bytes: # Space tone as bytes for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/0.wav")
    def getTxMark(self) -> bytes: # Mark tone as bytes for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/1.wav")
    def getRxSpace(self) -> list: # Space tone as int array for RX
        return self.__loadWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/0.wav")
    def getRxMark(self) -> list: # Mark tone as int array for RX
        return self.__loadWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/1.wav")
    def getRxTraining(self) -> list: # Ideal training sequence oscillation for RX clock recovery
        return self.getRxMark() + self.getRxSpace()

################################################################################ HAMMING ECC
class Hamming:
    def __init__(self): # non-static to keep track of errors
        self.r = 4
        self.errorCount = 0

    def resetErrorCount(self): # Reset error count to 0
        self.errorCount = 0
    
    def getErrorCount(self) -> int: # Get error count
        return self.errorCount
    
    def __incrementErrorCount(self):
        self.errorCount += 1
    
    # Pad the positions of parity bits with 0
    def __padParityBits(self, data: str) -> str:
        j = 0
        k = 1
        m = len(data)
        p = ''
        for i in range(1, m + self.r+1):
            if(i == 2**j):
                p += '0'
                j += 1
            else:
                p += data[-1 * k]
                k += 1
        return p[::-1]

    # Set the parity bits to their correct values
    def __setParityBits(self, data: str) -> str:
        n = len(data)
        for i in range(self.r):
            p = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    p = p ^ int(data[-1 * j])
            data = data[:n-(2**i)] + str(p) + data[n-(2**i)+1:]
        return data

    # Find an error (if it exists)
    def __getErrorIndex(self, data: str) -> int:
        n = len(data)
        p = 0
        for i in range(self.r):
            val = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    val = val ^ int(data[-1 * j])
            p += val*(10**i)
        return n - int(str(p), 2)

    # Trim the parity bits off a corrected message to get the contained data
    def __trimParityBits(self, data: str) -> str:
        data = data[::-1]
        p = ""
        j = 0
        for i in range(len(data)):
            if(i + 1 != 2 ** j):
                p += data[i]
            else:
                j += 1
        return p[::-1]

    # Correct a single error in a section of data.
    def __correctErrors(self, data: str) -> str:
        ePos = self.__getErrorIndex(data)
        if(ePos == len(data)):
            return data
        else:
            self.__incrementErrorCount()
            dataList = list(data)
            if(dataList[ePos] == "0"):
                dataList[ePos] = "1"
            else:
                dataList[ePos] = "0"
            data = "".join(dataList)
        return data

    # Single function handling generating Hamming code. Returns a tuple with the 
    # result bit string and the number of redundant bits.
    def encode(self, data: str) -> str:
        paddedData = self.__padParityBits(data)
        output = self.__setParityBits(paddedData)
        return(output)

    # Single function handling correcting and getting useful data from Hamming
    # code. Returns the data payload.
    def decode(self, data: str) -> str:
        correctedData = self.__correctErrors(data)
        output = self.__trimParityBits(correctedData)
        return(output)

################################################################################ RX TOOLS
class digitalReceiver:
    def __init__(self,
    dModType = digitalModulationTypes.default(),    
    ampStartThresh = AMPLITUDE_START_THRESHOLD,
    ampEndThresh = AMPLITUDE_END_THRESHOLD,
    recStartThresh = RECORDING_START_THRESHOLD,
    recEndThresh = RECORDING_END_THRESHOLD,
    ampDeadzone = AMPLIFIER_DEADZONE):
        self.dModType = dModType
        self.ampStartThresh = ampStartThresh
        self.ampEndThresh = ampEndThresh
        self.recStartThresh = recStartThresh
        self.recEndThresh = recEndThresh
        self.ampDeadzone = ampDeadzone
        self.unitTime = digitalModulationTypes.getUnitTime(self.dModType)
        self.crScanJump = int(self.unitTime * 64)
        self.crScanWidth = int(self.unitTime * 16)
        iw = idealWaves(digitalModulationType = self.dModType)
        self.rxSpace = iw.getRxSpace()
        self.rxMark = iw.getRxMark()
        self.rxTraining = iw.getRxTraining()
        self.ecc = Hamming()
    
    # Load raw wav data from file
    def __loadRawWavData(self, filename: str) -> bytes:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    # From sine to square
    def __amplifyChunk(self, chunk: list) -> list:
        ampChunk = []
        for i in chunk:
            if(i > self.ampDeadzone):
                ampChunk.append(32767)
            elif(i < -1 * self.ampDeadzone):
                ampChunk.append(-32767)
            else:
                ampChunk.append(0)
        return ampChunk

    # Absolute average deviation from bytes
    def __rawAbsDeviation(self, frames: bytes) -> int:
        sampFrames = []
        for i in range(len(frames) - 1): 
            sFrame = frames[i:i+2]
            sampFrames.append(abs(struct.unpack("<h", sFrame)[0]))
            i += 2
        return int(sum(sampFrames) / len(sampFrames))

    # Auto-record and return frames
    def __autoRecord(self, start_sensitivity: int, end_sensitivity: int, timeout=-1) -> bytes:
        timeoutIter = round(timeout * (SAMPLE_RATE/INPUT_FRAMES_PER_BLOCK))
        pa = pyaudio.PyAudio() # Open stream on PortAudio
        stream = pa.open(format=FORMAT, channels=CHANNELS,
                rate=SAMPLE_RATE, input=True,
                frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
        stream.read(INPUT_FRAMES_PER_BLOCK) # Flush buffer
        listenerIter = 0
        while (True):
            listenerIter += 1
            if(listenerIter > timeoutIter and timeout > 0):
                stream.stop_stream()
                stream.close()
                pa.terminate()
                log(1, "Listener timed out at " + timeout + "s.")
                return b''
            
            totFrames = []
            frames = stream.read(INPUT_FRAMES_PER_BLOCK) # Record and sample
            chunkAmp = self.__rawAbsDeviation(frames)
            if(chunkAmp > start_sensitivity): # Record and return
                log(0, "Start of transmission detected (Amplitude: " + str(chunkAmp) + "). Recording...")
                while(chunkAmp > end_sensitivity):
                    frames = stream.read(INPUT_FRAMES_PER_BLOCK)
                    totFrames.append(frames)
                    chunkAmp = self.__rawAbsDeviation(frames)
                log(0, "End of transmission detected (Amplitude: " + str(chunkAmp) + "). Listener finished.")
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return b''.join(totFrames)

    # Unsigned average deviation for full amplitude avgs
    def __absDeviation(self, chunk: list) -> int: 
        totFrames = 0
        for frame in chunk:
            totFrames += abs(frame)
        return int(totFrames / len(chunk))

    # Find the error between an ideal wave and a received wave
    def __compareSamples(self, idealSample: list, receivedSample: list) -> int: 
        diffArr = []
        for i in range(len(idealSample)):
            diffArr.append(abs(idealSample[i]-receivedSample[i]))
        return int(sum(diffArr) / len(diffArr))

    # Recover the clock from a chunk of audio by scanning the training sequence
    def __findStart(self, chunk: list) -> int:
        log(0, "Attempting to recover clock...")
        try:
            ampIndex = 0
            while(abs(chunk[ampIndex]) < self.ampStartThresh): # Find the rough start of the training block
                ampIndex += 1
            ampIndex += self.crScanJump # Jump into the training block and pull a sample for clock recovery
            fitChunk = chunk[(ampIndex-self.crScanWidth):(ampIndex+self.crScanWidth+self.unitTime*2)]
            fitChunk = self.__amplifyChunk(fitChunk) # Amplify our sample to fit it to ideal waves
            fitErrs = []
            for i in range(self.crScanWidth * 2): # Create an array of errors
                fitErrs.append(self.__compareSamples(self.rxTraining, fitChunk[i:i+self.unitTime * 2]))
            # Find the start index with the lowest error to recover the clock.
            startIndex = ampIndex - self.crScanWidth + fitErrs.index(min(fitErrs))
            log(0, "Clock recovered at sample " + str(startIndex) +".")
            return startIndex
        except Exception as e:
            log(1, "Failed to recover clock. Most likely bad transmission integrity.")
            return -1

    # Check if a chunk's value is 1 or 0 based on its frequency.
    def __getLogicValue(self, chunk: list) -> str:
        # Amplify received wave to approximate to a square wave
        ampChunk = self.__amplifyChunk(chunk)
        # Compare to ideal square waves
        markDev = self.__compareSamples(self.rxMark, ampChunk)
        spaceDev = self.__compareSamples(self.rxSpace, ampChunk)
        if(markDev < spaceDev):
            return "1"
        else:
            return "0"

    # Get bits from wav data
    def __getBitsFromWavData(self, wavFrames: bytes) -> str:
            expFrames = []
            binData = ""
            frameIter = 0
            while(frameIter < len(wavFrames) - 1): # Unpack data to array of amplitudes
                sFrame = wavFrames[frameIter:frameIter+2]
                expFrames.append(struct.unpack("<h", sFrame)[0])
                frameIter += 2
            nFrames = len(expFrames)

            startSample = self.__findStart(expFrames) # Recover the clock

            if(startSample == -1): # if no start sample could be found we can't decode
                return ""
            
            chunkIter = int(self.unitTime) + startSample # Decode to bits (including training block)
            while(chunkIter < nFrames - 1):
                chunk = expFrames[int(chunkIter - self.unitTime):int(chunkIter)]
                if(self.__absDeviation(chunk) < self.ampEndThresh): # End decode when no more data is being transmitted
                    break
                binData += self.__getLogicValue(chunk)
                chunkIter += self.unitTime
            return binData

    # Trim the training block off of received bits
    def __trimTrainingBlock(self, data: str) -> str:
        trainingBits = 0
        zeroStreak = 0
        endTrainingIndex = 0
        for i in range(len(data)-1):
            if(data[i] != data[i+1]):
                trainingBits += 1
            if(data[i] == "0"):
                zeroStreak += 1
                if(zeroStreak > 2 and trainingBits > 16):
                    endTrainingIndex = i + 1
                    break
            else:
                zeroStreak = 0
        return(data[endTrainingIndex::])

    # Convert bits to bytes
    def __getBytesFromBits(self, bData: str) -> bytes:
        intData = []
        i = 0
        while(i < len(bData)):
            intData.append(int(bData[(i):(i+8)], 2))
            i += 8
        return bytes(intData)
    
    # Run error correction and remove all parity bits from bits data
    def __getSourceDataFromECC(self, data: str) -> str:
        dataBytes = []
        decodedBytes = []
        dataIter = 0
        self.ecc.resetErrorCount()
        while(dataIter < len(data) - 11):
            dataBytes.append(data[dataIter:dataIter+12])
            dataIter += 12
        for dataByte in dataBytes:
            decodedBytes.append(self.ecc.decode(dataByte))
        output = "".join(decodedBytes)
        return output, self.ecc.getErrorCount()
    
    # One call to receive bytes data from default audio input (timeout in seconds, disabled by default)
    def rx(self, timeout=-1):
        log(0, "Receiver started.")
        wavData = self.__autoRecord(self.recStartThresh, self.recEndThresh, timeout)
        bd = self.__getBitsFromWavData(wavData)
        log(0, "Decoding waveform to digital data...")
        if(bd == ""): # if no good data
            log(1, "Decoding failed. No usable data found.")
            return b"", 0
        bd = self.__trimTrainingBlock(bd)
        decodedBin, errorCount = self.__getSourceDataFromECC(bd)
        bytesData = self.__getBytesFromBits(decodedBin)
        log(0, "Decoding successful. " + str(errorCount) + " bit-errors corrected.")
        return bytesData, errorCount
    
    # One call to receive bytes data from recording
    def rxFromWav(self, filename: str): 
        wavData = self.__loadRawWavData(filename)
        bd = self.__getBitsFromWavData(wavData)
        if(bd == ""): # if no good data
            return b""
        bd = self.__trimTrainingBlock(bd)
        decodedBin, errorCount = self.__getSourceDataFromECC(bd)
        bytesData = self.__getBytesFromBits(decodedBin)
        return bytesData, errorCount

################################################################################ TX TOOLS
class digitalTransmitter:
    def __init__(self, 
    dModType = digitalModulationTypes.default(),
    trainingSequenceTime = TRAINING_SEQUENCE_TIME):
        self.dModType = dModType
        self.tsOscillations = digitalModulationTypes.getTsOscillations(trainingSequenceTime, self.dModType)
        self.unitTime = digitalModulationTypes.getUnitTime(self.dModType)
        iw = idealWaves(digitalModulationType = self.dModType)
        self.txSpace = iw.getTxSpace()
        self.txMark = iw.getTxMark()
        self.txSilence = iw.getTxSilence()
        self.ecc = Hamming()

    # Get bits from bytes
    def __getBitsFromBytes(self, bIn: bytes) -> str:
        bBin = ""
        for i in range(len(bIn)):
            bBin += '{0:08b}'.format(bIn[i])
        return bBin

    # Encode bits to audio
    def __encode(self, bits: str) -> bytes:
        oFrames = []
        # Pad the start of the file with silence
        oFrames += self.txSilence
        # Write the data freqs to the file
        for bit in bits:
            if(bit == "0"):
                oFrames += self.txSpace
            else:
                oFrames += self.txMark
        # Pad the end of the file with silence
        oFrames += self.txSilence
        return bytes(oFrames)

    # Generate training block
    def __generateTrainingBlock(self) -> str:
        output = "10" * self.tsOscillations
        output += "1"
        output += "0" * 3
        return output

    # Generate and insert ECC into the data.
    def __insertECC(self, data: str) -> str:
        dataBytes = []
        encodedBytes = []
        dataIter = 0
        while(dataIter < len(data) - 7):
            dataBytes.append(data[dataIter:dataIter+8])
            dataIter += 8
        for dataByte in dataBytes:
            encodedBytes.append(self.ecc.encode(dataByte))
        output = "".join(encodedBytes)
        return(output)

    # Play a sound from wav data
    def __playWavData(self, data: bytes):
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format = FORMAT,
                channels = CHANNELS,
                rate = SAMPLE_RATE,
                output = True
            )
            stream.write(data)
            sleep(0.1) # let the player finish
            stream.close()
            stream.stop_stream()
            pa.terminate()

    # Save wav data as a file
    def __saveWavFile(self, data: bytes, filename: str):
        with wave.open(filename, 'wb') as f:
            f.setnchannels(CHANNELS)
            f.setsampwidth(pyaudio.get_sample_size(FORMAT))
            f.setframerate(SAMPLE_RATE)
            f.writeframes(data)

    def tx(self, data: bytes): # One call to send bytes data over default audio output
        log(0, "Encoding data for transmission...")
        messageBits = self.__getBitsFromBytes(data)
        eccBits = self.__insertECC(messageBits)
        trainingBlock = self.__generateTrainingBlock()
        txBits = trainingBlock + eccBits
        oAudio = self.__encode(txBits)
        log(0, "Transmitting...")
        self.__playWavData(oAudio)
        log(1, "Transmitter finished.")

    def txToWav(self, data: bytes, filename: str): # One call to record bytes data to file
        messageBits = self.__getBitsFromBytes(data)
        eccBits = self.__insertECC(messageBits)
        trainingBlock = self.__generateTrainingBlock()
        txBits = trainingBlock + eccBits
        oAudio = self.__encode(txBits)
        self.__saveWavFile(oAudio, filename)
    
    def estTxTime(self, dataLen: int): # est transmission time in seconds
        return (self.tsOscillations * 2 + dataLen * 12) / (SAMPLE_RATE / self.unitTime)
