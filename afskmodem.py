"""
x---------------------------------------x
| AFSKmodem v1.0                        |
| https://jvmeifert.github.io/afskmodem |
x---------------------------------------x
"""
import wave
import struct
import pyaudio
from time import sleep

################################################################################ PROGRAM DEFAULTS

# USER-CONFIGURABLE PARAMETERS: Although these should work fine as-is, fine-tuning them will not affect functionality.
#
# How many oscillations we transmit in a training sequence (Recommended 192-384, Default 192)
TRAINING_SEQUENCE_OSCILLATIONS = 192
#
# Instant amplitude required to recognize the training sequence (0-32768, Default 16384)
AMPLITUDE_START_THRESHOLD = 16384
#
# Chunk amplitude at which decoding stops (0-32768, Default 8192)
AMPLITUDE_END_THRESHOLD = 8192
#
# Chunk amplitude required to start recording (0-32768, Default 4096) * SQUELCH SHOULD BE ENABLED ON RX HARDWARE
RECORDING_START_THRESHOLD = 4096
#
# Chunk amplitude required to stop recording (0-32768, Default 2048) * SQUELCH SHOULD BE ENABLED ON RX HARDWARE
RECORDING_END_THRESHOLD = 2048
#
# Amplifier function deadzone (0-32768, Default 1024)
AMPLIFIER_DEADZONE = 1024

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
# Frames per buffer for input
INPUT_FRAMES_PER_BLOCK = 4096
#
# Directory where ideal waves are stored
IDEAL_WAVES_DIR = "data/ideal_waves/"

################################################################################ DIGITAL MODULATION TYPES
class digitalModulationTypes():
    def afsk500(): # Audio Frequency-Shift Keying (500 baud)
        return "afsk500"
    def afsk1000(): # Audio Frequency-Shift Keying (1000 baud)
        return "afsk1000"
    def default():
        return "afsk500"
    
    # Unit time in samples
    def getUnitTime(digitalModulationType):
        if(digitalModulationType == "afsk500"):
            return int(SAMPLE_RATE / 500)
        elif(digitalModulationType == "afsk1000"):
            return int(SAMPLE_RATE / 1000)
        else: # default
            return int(SAMPLE_RATE / 500)
        
################################################################################ IDEAL WAVES
class idealWaves(): # Ideal waves for TX and RX
    def __init__(self, digitalModulationType = digitalModulationTypes.default()):
        self.digitalModulationType = digitalModulationType

    # Load wav data to int array
    def __loadWavData(self,filename):
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            expFrames = []
            for i in range(0, nFrames):
                sFrame = f.readframes(1)
                expFrames.append(struct.unpack("<h", sFrame)[0])
            return expFrames

    # Load wav data to byte array
    def __loadRawWavData(self,filename):
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    def getTxSilence(self): # Silence (200ms) to pad output with for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + "_.wav")
    def getTxSpace(self): # Space tone as bytes for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/0.wav")
    def getTxMark(self): # Mark tone as bytes for TX
        return self.__loadRawWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/1.wav")
    def getRxSpace(self): # Space tone as int array for RX
        return self.__loadWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/0.wav")
    def getRxMark(self): # Mark tone as int array for RX
        return self.__loadWavData(IDEAL_WAVES_DIR + self.digitalModulationType + "/1.wav")
    def getRxTraining(self): # Ideal training sequence oscillation for RX clock recovery
        return self.getRxMark() + self.getRxSpace()

################################################################################ HAMMING ECC
class hammingECC():
    def __init__(self, r = 4): # 4 default for per-byte ecc
        self.r = r
        self.errorCount = 0
    
    # Number of parity bits to be added to a bit string of a given length m (a byte gets 4)
    def getParityBitsAmt(self, data):
        for i in range(len(data)):
            if(2**i >= len(data) + i + 1):
                return i

    def resetErrorCount(self): # Error count utils
        self.errorCount = 0
    def incrementErrorCount(self):
        self.errorCount += 1
    def getErrorCount(self):
        return self.errorCount
    
    # Pad the positions of parity bits with a logical 0
    def __padParityBitsPos(self, data):
        j = 0
        k = 1
        m = len(data)
        res = ''
        for i in range(1, m + self.r+1):
            if(i == 2**j):
                res = res + '0'
                j += 1
            else:
                res = res + data[-1 * k]
                k += 1
        return res[::-1]

    # Set the parity bits to their correct values
    def __insertParityBits(self, data):
        n = len(data)
        for i in range(self.r):
            val = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    val = val ^ int(data[-1 * j])
            data = data[:n-(2**i)] + str(val) + data[n-(2**i)+1:]
        return data

    # Find an error (if it exists)
    def __getErrorPos(self, data):
        n = len(data)
        res = 0
        for i in range(self.r):
            val = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    val = val ^ int(data[-1 * j])
            res = res + val*(10**i)
        return n - int(str(res), 2)

    # Trim the parity bits off a corrected message to get the contained data
    def __removeParityBits(self, data):
        data = data[::-1]
        output = ""
        j = 0
        for i in range(len(data)):
            if(i + 1 != 2 ** j):
                output += data[i]
            else:
                j += 1
        return output[::-1]

    # Correct a single error in a section of data.
    def __correctErrors(self, data):
        ePos = self.__getErrorPos(data)
        if(ePos == len(data)):
            return data
        else:
            self.incrementErrorCount()
            dataList = list(data)
            if(dataList[ePos] == "0"):
                dataList[ePos] = "1"
            else:
                dataList[ePos] = "0"
            data = "".join(dataList)
        return data

    # Single function handling generating Hamming code. Returns a tuple with the 
    # result bit string and the number of redundant bits.
    def encode(self, data):
        paddedData = self.__padParityBitsPos(data)
        output = self.__insertParityBits(paddedData)
        return(output)

    # Single function handling correcting and getting useful data from Hamming
    # code. Returns the data payload.
    def decode(self, data):
        fixedData = self.__correctErrors(data)
        output = self.__removeParityBits(fixedData)
        return(output)

################################################################################ RX TOOLS
class digitalReceiver():
    def __init__(self,
    digitalModulationType = digitalModulationTypes.default(),    
    amplitudeStartThreshold = AMPLITUDE_START_THRESHOLD,
    amplitudeEndThreshold = AMPLITUDE_END_THRESHOLD,
    recordingStartThreshold = RECORDING_START_THRESHOLD,
    recordingEndThreshold = RECORDING_END_THRESHOLD,
    amplifierDeadzone = AMPLIFIER_DEADZONE):
        self.digitalModulationType = digitalModulationType
        self.amplitudeStartThreshold = amplitudeStartThreshold
        self.amplitudeEndThreshold = amplitudeEndThreshold
        self.recordingStartThreshold = recordingStartThreshold
        self.recordingEndThreshold = recordingEndThreshold
        self.amplifierDeadzone = amplifierDeadzone
        self.unitTime = digitalModulationTypes.getUnitTime(self.digitalModulationType)
        self.ClockRecoveryScanJump = int(self.unitTime * 64)
        self.ClockRecoveryScanWidth = int(self.unitTime * 16)
        iw = idealWaves(digitalModulationType = self.digitalModulationType)
        self.rxSpace = iw.getRxSpace()
        self.rxMark = iw.getRxMark()
        self.rxTraining = iw.getRxTraining()
        self.ecc = hammingECC()
    
    # Load raw wav data from file
    def __loadRawWavData(self,filename):
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    # From sine to square
    def __amplifyChunk(self, chunk):
        ampChunk = []
        for i in chunk:
            if(i > self.amplifierDeadzone):
                ampChunk.append(32767)
            elif(i < -1 * self.amplifierDeadzone):
                ampChunk.append(-32767)
            else:
                ampChunk.append(0)
        return ampChunk

    # Quick sampling amplitude
    def __quickAvgAmp(self, frames, step=64):
        frameIter = 0
        sampFrames = []
        while(frameIter < len(frames) - 1): 
            sFrame = frames[frameIter:frameIter+2]
            sampFrames.append(abs(struct.unpack("<h", sFrame)[0]))
            frameIter += step
        return sum(sampFrames) / len(sampFrames)

    # Auto-record and return frames
    def __autoRecord(self, start_sensitivity, end_sensitivity, timeout=-1):
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
                return ""
            
            totFrames = []
            frames = stream.read(INPUT_FRAMES_PER_BLOCK) # Record and sample
            chunkAmp = self.__quickAvgAmp(frames)
            if(chunkAmp > start_sensitivity): # Record and return
                while(chunkAmp > end_sensitivity):
                    frames = stream.read(INPUT_FRAMES_PER_BLOCK)
                    totFrames.append(frames)
                    chunkAmp = self.__quickAvgAmp(frames)
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return b''.join(totFrames)

    # Unsigned average deviation for full amplitude avgs
    def __absDeviation(self, chunk): 
        totFrames = 0
        for frame in chunk:
            totFrames += abs(frame)
        return totFrames / len(chunk)

    # Find the error between an ideal wave and a received wave
    def __compareSamples(self, idealSample, receivedSample): 
        diffArr = []
        for i in range(len(idealSample)):
            diffArr.append(abs(idealSample[i]-receivedSample[i]))
        return sum(diffArr) / len(diffArr)

    # Recover the clock from a chunk of audio by scanning the training sequence
    def __findStart(self, chunk):
        try:
            ampIndex = 0
            while(abs(chunk[ampIndex]) < self.amplitudeStartThreshold): # Find the rough start of the training block
                ampIndex += 1
            ampIndex += self.ClockRecoveryScanJump # Jump into the training block and pull a sample for clock recovery
            fitChunk = chunk[(ampIndex-self.ClockRecoveryScanWidth):(ampIndex+self.ClockRecoveryScanWidth+self.unitTime*2)]
            fitChunk = self.__amplifyChunk(fitChunk) # Amplify our sample to fit it to ideal waves
            fitErrs = []
            for i in range(self.ClockRecoveryScanWidth * 2): # Create an array of errors
                fitErrs.append(self.__compareSamples(self.rxTraining, fitChunk[i:i+self.unitTime * 2]))
            # Find the start index with the lowest error to recover the clock.
            startIndex = ampIndex - self.ClockRecoveryScanWidth + fitErrs.index(min(fitErrs))
            return startIndex
        except Exception as e:
            return -1

    # Check if a chunk's value is 1 or 0 based on its frequency.
    def __getLogicValue(self, chunk):
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
    def __getBitsFromWavData(self, wavFrames):
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
                if(self.__absDeviation(chunk) < self.amplitudeEndThreshold): # End decode when no more data is being transmitted
                    break
                binData += self.__getLogicValue(chunk)
                chunkIter += self.unitTime
            return binData

    # Trim the training block off of received bits
    def __trimTrainingBlock(self, data):
        trainingBits = 0
        zeroStreak = 0
        endTrainingIndex = 0
        for i in range(len(data)-1):
            if(data[i] != data[i+1]):
                trainingBits += 1
            if(data[i] == "0"):
                zeroStreak += 1
                if(zeroStreak > 4 and trainingBits > 16):
                    endTrainingIndex = i + 1
                    break
            else:
                zeroStreak = 0
        return(data[endTrainingIndex::])

    # Convert bits to bytes
    def __getBytesFromBits(self, binaryData):
        intData = []
        i = 0
        while(i < len(binaryData)):
            intData.append(int(binaryData[(i):(i+8)], 2))
            i += 8
        return bytes(intData)
    
    # Run error correction and remove all parity bits from bits data
    def __getSourceDataFromECC(self, data):
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
        wavData = self.__autoRecord(self.recordingStartThreshold, self.recordingEndThreshold, timeout)
        bd = self.__getBitsFromWavData(wavData)
        if(bd == ""): # if no good data
            return b"", 0
        bd = self.__trimTrainingBlock(bd)
        decodedBin, errorCount = self.__getSourceDataFromECC(bd)
        bytesData = self.__getBytesFromBits(decodedBin)
        return bytesData, errorCount
    
    # One call to receive bytes data from recording
    def rxFromWav(self, filename): 
        wavData = self.__loadRawWavData(filename)
        bd = self.__getBitsFromWavData(wavData)
        if(bd == ""): # if no good data
            return b""
        bd = self.__trimTrainingBlock(bd)
        decodedBin, errorCount = self.__getSourceDataFromECC(bd)
        bytesData = self.__getBytesFromBits(decodedBin)
        return bytesData, errorCount

################################################################################ TX TOOLS
class digitalTransmitter():
    def __init__(self, 
    digitalModulationType = digitalModulationTypes.default(),
    trainingSequenceOscillations = TRAINING_SEQUENCE_OSCILLATIONS):
        self.digitalModulationType = digitalModulationType
        self.trainingSequenceOscillations = trainingSequenceOscillations
        self.unitTime = digitalModulationTypes.getUnitTime(self.digitalModulationType)
        iw = idealWaves(digitalModulationType = self.digitalModulationType)
        self.txSpace = iw.getTxSpace()
        self.txMark = iw.getTxMark()
        self.txSilence = iw.getTxSilence()
        self.ecc = hammingECC()

    # Get bits from bytes
    def __getBitsFromBytes(self, bytesIn):
        bBin = ""
        for i in range(len(bytesIn)):
            bBin += '{0:08b}'.format(bytesIn[i])
        return bBin

    # Encode bits to audio
    def __encode(self, bits):
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
    def __generateTrainingBlock(self):
        output = "10" * self.trainingSequenceOscillations
        output += "1"
        output += "0" * 5
        return output

    # Generate and insert ECC into the data.
    def __insertECC(self, data):
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
    def __playWavData(self, data):
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
    def __saveWavFile(self, data,filename):
        with wave.open(filename, 'wb') as f:
            f.setnchannels(CHANNELS)
            f.setsampwidth(pyaudio.get_sample_size(FORMAT))
            f.setframerate(SAMPLE_RATE)
            f.writeframes(data)

    def tx(self, data): # One call to send bytes data over default audio output
        messageBits = self.__getBitsFromBytes(data)
        eccBits = self.__insertECC(messageBits)
        trainingBlock = self.__generateTrainingBlock()
        txBits = trainingBlock + eccBits
        oAudio = self.__encode(txBits)
        self.__playWavData(oAudio)

    def txToWav(self, data, filename): # One call to record bytes data to file
        messageBits = self.__getBitsFromBytes(data)
        eccBits = self.__insertECC(messageBits)
        trainingBlock = self.__generateTrainingBlock()
        txBits = trainingBlock + eccBits
        oAudio = self.__encode(txBits)
        self.__saveWavFile(oAudio, filename)
    
    def estTxTime(self, dataLen): # est transmission time in seconds
        return (self.trainingSequenceOscillations * 2 + dataLen * 12) / (SAMPLE_RATE / self.unitTime)
