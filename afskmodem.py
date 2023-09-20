"""
  afskmodem.py
  https://lavajuno.github.io/afskmodem
  Author: Juno Meifert
"""

import wave
import struct
import pyaudio
from datetime import datetime
import os
from time import sleep

##### Constants #####

##### USER PARAMETERS: Although these should work fine as-is, 
##### tuning them will not affect functionality.

# Training sequence time in seconds (0.5-1.0, Default 0.6)
TRAINING_SEQUENCE_TIME = 0.6

# Chunk amplitude at which decoding starts (0-32768, Default 18000 [-5.2 dBfs])
AMPLITUDE_START_THRESHOLD = 18000

# Chunk amplitude at which decoding stops (0-32768, Default 14000 [-7.4 dBfs])
AMPLITUDE_END_THRESHOLD = 14000

# Amplifier function deadzone (0-32768, Default 128 [-48.2 dBfs])
AMPLIFIER_DEADZONE = 128


##### PROGRAM CONSTANTS: DO NOT CHANGE THESE!

# Frames per buffer for audio input (Default 2048 [0.043s])
INPUT_FRAMES_PER_BLOCK = 2048

# Recording/playback sample rate
SAMPLE_RATE = 48000

# Recording/playback format
FORMAT = pyaudio.paInt16

# Recording/playback channels
CHANNELS = 1

# Frames to scan for clock recovery (Should scan at least two full blocks in,
# but no more than a portion of the length of the training sequence.)
CLOCK_SCAN_WIDTH = 2 * INPUT_FRAMES_PER_BLOCK

# Directory where waveforms are stored
WAVEFORMS_DIR = "waveforms/"

"""
    Logging functionality
"""
def get_date_and_time(): # Long date and time for logging
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Logging level (0: INFO, 1: WARN (recommended), 2: ERROR, 3: NONE)
LOG_LEVEL = 0
#
# Should the log output to the console?
LOG_TO_CONSOLE = True
#
# Should the log output to a log file?
LOG_TO_FILE = False
#
# Where to generate logfile if need be
LOG_PATH = "afskmodem.log"
#
# How the log identifies which module is logging.
LOG_PREFIX = "(AFSKmodem)"

# Initialize log file if needed
if(LOG_TO_FILE):
    try:
        os.remove(LOG_PATH)
    except:
        pass
    with open(LOG_PATH, "w") as f:
        f.write(get_date_and_time() + 
                " [  OK  ] " + LOG_PREFIX + " Logging initialized.\n")

# Prints a message to enabled log outputs with the given level.
def log(level: int, data: str):
    if(level >= LOG_LEVEL):
        output = get_date_and_time()
        if(level == 0):
            output += " [  OK  ] "
        elif(level == 1):
            output += " [ WARN ] "
        else:
            output += " [ERROR!] "
        output += LOG_PREFIX + " "
        output += data
        if(LOG_TO_FILE):
            with open(LOG_PATH, "a") as f:
                f.write(output + "\n")
        if(LOG_TO_CONSOLE):
            print(output)

"""
    DigitalModes defines the speeds at which AFSKmodem can operate, 
    and the tones that they use.
"""
class DigitalModes:
    # Audio Frequency-Shift Keying (300 baud)
    def afsk300() -> str: 
        return "afsk300"

    # Audio Frequency-Shift Keying (600 baud)
    def afsk600() -> str: 
        return "afsk600"
    
    # Audio Frequency-Shift Keying (1200 baud)
    def afsk1200() -> str: 
        return "afsk1200"

    # Audio Frequency-Shift Keying (2400 baud)
    def afsk2400() -> str: 
        return "afsk2400"

    # Audio Frequency-Shift Keying (6000 baud)
    def afsk6000() -> str: 
        return "afsk6000"

    # Default (AFSK1200)
    def default() -> str: 
        return "afsk1200"
    
    # Returns the unit time in samples of the given mode
    def getUnitTime(digital_mode: str) -> int:
        if(digital_mode == "afsk300"):
            return int(SAMPLE_RATE / 300)
        elif(digital_mode == "afsk600"):
            return int(SAMPLE_RATE / 600)
        elif(digital_mode == "afsk1200"):
            return int(SAMPLE_RATE / 1200)
        elif(digital_mode == "afsk2400"):
            return int(SAMPLE_RATE / 2400)
        elif(digital_mode == "afsk6000"):
            return int(SAMPLE_RATE / 6000)
        else: # default
            return int(SAMPLE_RATE / 1200)

    # Returns the number of training sequence oscillations 
    # for a specified time
    def getTrainingCycles(sequence_time: int, digital_mode: str) -> int:
        if(digital_mode == "afsk300"):
            return int(300 * sequence_time / 2)
        elif(digital_mode == "afsk600"):
            return int(600 * sequence_time / 2)
        elif(digital_mode == "afsk1200"):
            return int(1200 * sequence_time / 2)
        elif(digital_mode == "afsk2400"):
            return int(2400 * sequence_time / 2)
        elif(digital_mode == "afsk6000"):
            return int(6000 * sequence_time / 2)
        else: # default
            return int(1200 * sequence_time / 2)
    
    # Get the frequency of the space tone for a given mode
    def getSpaceTone(digital_mode: str) -> int:
        if(digital_mode == "afsk300"):
            return 300
        elif(digital_mode == "afsk600"):
            return 600
        elif(digital_mode == "afsk1200"):
            return 1200
        elif(digital_mode == "afsk2400"):
            return 2400
        elif(digital_mode == "afsk6000"):
            return 6000
        else: # default
            return 1200

    # Get the frequency of the mark tone for a given mode
    def getMarkTone(digital_mode: str) -> int:
        if(digital_mode == "afsk300"):
            return 600
        elif(digital_mode == "afsk600"):
            return 1200
        elif(digital_mode == "afsk1200"):
            return 2400
        elif(digital_mode == "afsk2400"):
            return 4800
        elif(digital_mode == "afsk6000"):
            return 12000
        else: # default
            return 2400

"""
    IdealWaves provides functions to load waveforms from files and return them 
    as lists of amplitudes, stored as either bytes or ints.
"""
class IdealWaves:
    def __init__(self, digital_mode = DigitalModes.default()):
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

"""
    Hamming provides functions related to error correction functionality and
    bit-error tracking.
"""
class Hamming:
    # Each instance of Hamming keeps track of the errors it corrects. 
    # An instance of Hamming is created for each DigitalTransmitter 
    # or DigitalReceiver instance.
    def __init__(self): 
        self.r = 4
        self.error_count = 0

    # Reset error count to 0
    def resetErrorCount(self):
        self.error_count = 0
    
    # Get error count
    def getErrorCount(self) -> int:
        return self.error_count
    
    # Pad the positions of parity bits with 0s
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
            k = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    k = k ^ int(data[-1 * j])
            p += k*(10**i)
        return n - int(str(p), 2)

    # Trim the parity bits off a corrected chunk to get the data only
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
        error_pos = self.__getErrorIndex(data)
        if(error_pos == len(data)):
            return data
        else:
            self.error_count += 1
            data_list = list(data)
            if(data_list[error_pos] == "0"):
                data_list[error_pos] = "1"
            else:
                data_list[error_pos] = "0"
            data = "".join(data_list)
        return data

    # Encodes a section of data.
    def encode(self, data: str) -> str:
        padded_data = self.__padParityBits(data)
        parity_data = self.__setParityBits(padded_data)
        return(parity_data)

    # Corrects and decodes a section of data.
    def decode(self, data: str) -> str:
        corrected_data = self.__correctErrors(data)
        output_data = self.__trimParityBits(corrected_data)
        return(output_data)

"""
    DigitalReceiver is a user-defined receiver class that provides functionality 
    for receiving and decoding messages.
"""
class DigitalReceiver:
    def __init__(self,
    digital_mode = DigitalModes.default(),    
    amp_start_threshold = AMPLITUDE_START_THRESHOLD,
    amp_end_threshold = AMPLITUDE_END_THRESHOLD,
    amp_deadzone = AMPLIFIER_DEADZONE):
        self.digital_mode = digital_mode
        self.amp_start_threshold = amp_start_threshold
        self.amp_end_threshold = amp_end_threshold
        self.amp_deadzone = amp_deadzone
        self.unit_time = DigitalModes.getUnitTime(self.digital_mode)
        self.space_tone = DigitalModes.getSpaceTone(self.digital_mode)
        self.mark_tone = DigitalModes.getMarkTone(self.digital_mode)
        ideal_waves = IdealWaves(self.digital_mode)
        self.rx_space = ideal_waves.getRxSpace()
        self.rx_mark = ideal_waves.getRxMark()
        self.rx_training = ideal_waves.getRxTraining()
        self.ecc = Hamming()
    
    # Amplifies a chunk of audio for decoding
    def __amplifyChunk(self, chunk: list[int]) -> list[int]:
        amp_chunk = []
        for i in chunk:
            if(i > self.amp_deadzone):
                amp_chunk.append(32767)
            elif(i < -1 * self.amp_deadzone):
                amp_chunk.append(-32767)
            else:
                amp_chunk.append(0)
        return amp_chunk

    # Calculates the unsigned average deviation of an audio sample (bytes)
    def __avgDeviationBytes(self, frames: bytes) -> int:
        s_frames = []
        for i in range(len(frames) - 1): 
            s_frame = frames[i:i+2]
            s_frames.append(abs(struct.unpack("<h", s_frame)[0]))
            i += 2
        return int(sum(s_frames) / len(s_frames))
    
    # Calculates the unsigned average deviation of an audio sample (ints)
    def __avgDeviationInts(self, chunk: list[int]) -> int: 
        frame_sum = 0
        for frame in chunk:
            frame_sum += abs(frame)
        return int(frame_sum / len(chunk))

    # Listen for a signal and return the recording to be decoded
    def __listen(self, timeout_seconds=-1) -> bytes:
        timeout_iters = round(timeout_seconds * 
                              (SAMPLE_RATE/INPUT_FRAMES_PER_BLOCK))
        pa = pyaudio.PyAudio() # Open an input stream with PortAudio
        stream = pa.open(format=FORMAT, channels=CHANNELS,
                rate=SAMPLE_RATE, input=True,
                frames_per_buffer=INPUT_FRAMES_PER_BLOCK)
        stream.read(INPUT_FRAMES_PER_BLOCK) # Flush input buffer
        listener_iters = 0
        while (True):
            listener_iters += 1
            if(listener_iters > timeout_iters and timeout_seconds > 0):
                # Close stream and return nothing if timeout is reached
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return b''
            
            recorded_frames = []
            # Listen and sample
            block_frames = stream.read(INPUT_FRAMES_PER_BLOCK)
            chunk_amplitude = self.__avgDeviationBytes(block_frames)
            # Record if we hear a signal
            if(chunk_amplitude > self.amp_start_threshold):
                while(chunk_amplitude > self.amp_end_threshold):
                    # Record until we no longer hear a signal
                    block_frames = stream.read(INPUT_FRAMES_PER_BLOCK)
                    recorded_frames.append(block_frames)
                    chunk_amplitude = self.__avgDeviationBytes(block_frames)
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return b''.join(recorded_frames)

    # Calculate the difference between an ideal waveform and a received waveform
    def __compareWaveforms(self, ideal_sample: list[int], 
                           given_sample: list[int]) -> int: 
        differences = []
        for i in range(len(ideal_sample)):
            differences.append(abs(ideal_sample[i] - given_sample[i]))
        return int(sum(differences) / len(differences))

    # Recover the clock from a chunk of audio by scanning the training sequence
    def __recoverClockIndex(self, chunk: list[int]) -> int:
        try:
            fit_chunk = self.__amplifyChunk(chunk[0:CLOCK_SCAN_WIDTH]) 
            fit_devs = []
            # Create an array of deviations
            for i in range(len(fit_chunk) - self.unit_time * 2 - 1): 
                fit_devs.append(self.__compareWaveforms(
                    self.rx_training, fit_chunk[i:i+self.unit_time * 2]))
            # Optimize the error for the best start sample index
            start_index = fit_devs.index(min(fit_devs))
            return start_index

        except Exception as e:
            # Catch most often an out-of-bounds exception 
            # indicating not enough good data (TODO improve error handling)
            return -1

    # Decide if a sample represents a 1 or 0
    def __getBitValue(self, chunk: list[int]) -> str:
        # Amplify received wave to approximate to a square wave
        amp_chunk = self.__amplifyChunk(chunk)
        # Compare to ideal square waves
        mark_diff = self.__compareWaveforms(self.rx_mark, amp_chunk)
        space_diff = self.__compareWaveforms(self.rx_space, amp_chunk)
        if(mark_diff < space_diff):
            return "1"
        else:
            return "0"

    # Decode bits from an audio sample
    def __decodeBits(self, frames: bytes) -> str:
            exp_frames = []
            bits = ""
            frame_iter = 0
            # Unpack bytes data to array of amplitudes
            while(frame_iter < len(frames) - 1): 
                s_frame = frames[frame_iter:frame_iter+2]
                exp_frames.append(struct.unpack("<h", s_frame)[0])
                frame_iter += 2
            nFrames = len(exp_frames)

            # Recover the clock
            start_sample = self.__recoverClockIndex(exp_frames) 
            
            # If no start sample could be found we can't decode
            if(start_sample == -1): 
                return ""
            
            # Decode to bits (including training block, we'll trim it off later)
            chunk_iter = int(self.unit_time) + start_sample 
            while(chunk_iter < nFrames - 1):
                chunk = exp_frames[int(chunk_iter - self.unit_time):int(chunk_iter)]
                # End decode when no more data is being transmitted
                if(self.__avgDeviationInts(chunk) < self.amp_end_threshold): 
                    break
                bits += self.__getBitValue(chunk)
                chunk_iter += self.unit_time
            return bits

    # Trim the remaining training sequence off of received bits
    def __trimTrainingSeq(self, data: str) -> str:
        training_bits = 0
        zero_count = 0
        end_training_index = 0
        for i in range(len(data)-1):
            if(data[i] != data[i+1]):
                training_bits += 1
            if(data[i] == "0"):
                zero_count += 1
                if(zero_count > 2 and training_bits > 16):
                    end_training_index = i + 1
                    break
            else:
                zero_count = 0
        return(data[end_training_index::])

    # Convert bits to bytes
    def __bitsToBytes(self, b_data: str) -> bytes:
        int_data = []
        i = 0
        while(i < len(b_data)):
            int_data.append(int(b_data[(i):(i+8)], 2))
            i += 8
        return bytes(int_data)
    
    # Run error correction and remove all parity bits
    def __correctErrors(self, data: str) -> str:
        data_bytes = []
        decoded_bytes = []
        data_iter = 0
        self.ecc.resetErrorCount()
        while(data_iter < len(data) - 11):
            data_bytes.append(data[data_iter:data_iter+12])
            data_iter += 12
        for i in data_bytes:
            decoded_bytes.append(self.ecc.decode(i))
        output = "".join(decoded_bytes)
        return output, self.ecc.getErrorCount()
    
    # Receives data and returns it (or fails)
    def rx(self, timeout = -1):
        log(0, "Receiver - listening...")
        recv_wav = self.__listen(timeout)
        if(recv_wav == b""): # if timed out
            log(1, "Receiver - timed out.")
            return b"", 0
        recv_bits = self.__decodeBits(recv_wav)
        if(recv_bits == ""): # if no good data
            log(1, "Receiver - bad data.")
            return b"", 0
        recv_bits = self.__trimTrainingSeq(recv_bits)
        decoded_bin, error_count = self.__correctErrors(recv_bits)
        bytes_data = self.__bitsToBytes(decoded_bin)
        log(0, "Receiver - done.")
        return bytes_data, error_count

"""
    DigitalTransmitter is a user-defined transmitter class that provides
    functionality for encoding and sending messages.
"""
class DigitalTransmitter:
    def __init__(self, 
    digital_modulation_type = DigitalModes.default(),
    training_sequence_time = TRAINING_SEQUENCE_TIME):
        self.digital_modulation_type = digital_modulation_type
        self.ts_cycles = DigitalModes.getTrainingCycles(
            training_sequence_time, self.digital_modulation_type)
        self.unit_time = DigitalModes.getUnitTime(self.digital_modulation_type)
        ideal_waves = IdealWaves(digital_mode = self.digital_modulation_type)
        self.tx_space = ideal_waves.getTxSpace()
        self.tx_mark = ideal_waves.GetTxMark()
        self.tx_silence = ideal_waves.getTxSilence()
        self.ecc = Hamming()

    # Convert bytes to bits
    def __bytesToBits(self, b_in: bytes) -> str:
        bits = ""
        for i in range(len(b_in)):
            bits += '{0:08b}'.format(b_in[i])
        return bits

    # Encode bits to audio
    def __encodeBits(self, bits: str) -> bytes:
        out_frames = []
        # Pad the start with silence
        out_frames += self.tx_silence
        # Write out bits as space and mark tones
        for bit in bits:
            if(bit == "0"):
                out_frames += self.tx_space
            else:
                out_frames += self.tx_mark
        # Pad the end with silence
        out_frames += self.tx_silence
        return bytes(out_frames)

    # Generate training sequence bits
    def __getTrainingBlock(self) -> str:
        output = "10" * self.ts_cycles
        output += "1"
        output += "0" * 3
        return output

    # Generate ECC and insert into data.
    def __generateECC(self, data: str) -> str:
        data_bytes = []
        encoded_bytes = []
        dataIter = 0
        while(dataIter < len(data) - 7):
            data_bytes.append(data[dataIter:dataIter+8])
            dataIter += 8
        for dataByte in data_bytes:
            encoded_bytes.append(self.ecc.encode(dataByte))
        output = "".join(encoded_bytes)
        return(output)

    # Play a waveform
    def __playWaveform(self, data: bytes):
            # Open an output stream with PortAudio
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format = FORMAT,
                channels = CHANNELS,
                rate = SAMPLE_RATE,
                output = True
            )
            # Write data to the stream
            stream.write(data)
            sleep(0.1) # let the stream finish
            stream.close()
            stream.stop_stream()
            pa.terminate()

    # Transmits the given data.
    def tx(self, data: bytes): 
        log(0, "Transmitter - sending " + str(len(data)) + " bytes...")
        message_bits = self.__bytesToBits(data)
        ecc_bits = self.__generateECC(message_bits)
        training_block = self.__getTrainingBlock()
        tx_bits = training_block + ecc_bits
        out_frames = self.__encodeBits(tx_bits)
        self.__playWaveform(out_frames)
        log(0, "Transmitter - done.")
    
    # Estimate transmission time in seconds
    def estimateTxTime(self, length: int): 
        return (self.ts_cycles * 2 + length * 12) / (SAMPLE_RATE / self.unit_time)
