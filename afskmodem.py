"""
  afskmodem.py
  https://lavajuno.github.io/afskmodem
  Author: Juno Meifert
"""

import wave
import struct
import pyaudio
from datetime import datetime
from time import sleep

# ----- Constants -----

# USER PARAMETERS: Although these should work fine as-is, 
# tuning them will not affect functionality.

# Log level (0: Info (Recommended), 1: Warn, 2: Error, 3: None)
LOG_LEVEL = 0

# Training sequence time in seconds (0.5-1.0, Default 0.6)
TRAINING_SEQUENCE_TIME = 0.6

# Amplitude at which decoding starts (0-32768, Default 18000 [-5.2 dBfs])
AMP_START_THRESHOLD = 18000

# Amplitude at which decoding stops (0-32768, Default 14000 [-7.4 dBfs])
AMP_END_THRESHOLD = 14000

# Amplitude function deadzone (0-32768, Default 128 [-48.2 dBfs])
AMP_DEADZONE = 128

# PROGRAM CONSTANTS: Do not change these!

# Frames per chunk for audio input
CHUNK_FRAMES = 2048

# Recording/playback sample rate
SAMPLE_RATE = 48000

# Recording/playback format
FORMAT = pyaudio.paInt16

# Recording/playback channels
CHANNELS = 1

# How far in to scan for clock recovery
CLOCK_SCAN_WIDTH = 2 * CHUNK_FRAMES

# Directory where waveforms are stored
WAVEFORMS_DIR = "waveforms/"

"""
    Log provides simple logging functionality.
"""
class Log:
    # Prints a log event
    def print(level: int, message: str):
        if(level >= LOG_LEVEL):
            output = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if(level == 0):
                output += " [ INFO ] "
            elif(level == 1):
                output += " [ WARN ] "
            else:
                output += " [ERROR!] "
            output += "(AFSKmodem) "
            output += message
            print(output)

"""
    DigitalModes defines the speeds at which AFSKmodem can operate, 
    and the tones that each speed uses.
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
    Waveforms provides functions to load waveforms from files and return them 
    as lists of amplitudes, stored as either bytes or ints.
    It is instantiated with a digital mode from the class DigitalModes.
"""
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

"""
    ECC provides functionality for encoding, decoding, and correcting
    bit errors.
"""
class ECC:
    __M_GENERATOR: list[list[int]] = [
            [1, 1, 0, 1],
            [1, 0, 1, 1],
            [1, 0, 0, 0],
            [0, 1, 1, 1],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
    ]

    __M_PARITY: list[list[int]] = [
            [1, 0, 1, 0, 1, 0, 1],
            [0, 1, 1, 0, 0, 1, 1],
            [0, 0, 0, 1, 1, 1, 1]
    ]

    # Multiplies a matrix and vector modulo 2
    def __multiply(a: list[list[int]], b: list[int]) -> list[int]:
        result: list[int] = [0] * len(a)
        for i in range(0, len(a)):
            for j in range(0, len(b)):
                result[i] += a[i][j] * b[j]
            result[i] %= 2
        return result
    
    # Encodes 4 data bits
    def __encodeNibble(data: list[int]) -> list[int]:
        return ECC.__multiply(ECC.__M_GENERATOR, data)

    # Decodes 4 data bits
    def __decodeNibble(data: list[int]) -> list[int]:
        syn: list[int] = ECC.__multiply(ECC.__M_PARITY, data)
        error_pos: int = syn[2] * 4 + syn[1] * 2 + syn[0]
        res: list[int] = data
        if(error_pos != 0):
            res[error_pos - 1] = 0 if res[error_pos - 1] == 1 else 1
        return [res[2], res[4], res[5], res[6]]

    # Corrects errors and decodes data. Returns decoded bits.
    def decode(bits: str) -> list[str]:
        dec_bits = ""
        for i in range(0, len(bits) - 6, 7):
            raw_bits: list[int] = []
            for j in bits[i : i + 7]:
                raw_bits.append(0 if j == "0" else 1)
            dec_nibble = ECC.__decodeNibble(raw_bits)
            for j in dec_nibble:
                dec_bits += "0" if j == 0 else "1"
        return dec_bits
    
    # Encodes data by inserting parity bits
    def encode(bits: str) -> str:
        enc_bits = ""
        for i in range(0, len(bits) - 3, 4):
            raw_bits: list[int] = []
            for j in bits[i : i + 4]:
                raw_bits.append(0 if j == "0" else 1)
            enc_nibble = ECC.__encodeNibble(raw_bits)
            for j in enc_nibble:
                enc_bits += "0" if j == 0 else "1"
        return enc_bits

"""
    DigitalReceiver is a user-defined receiver class that provides functionality 
    for receiving and decoding messages.
    It is instantiated with a digital mode from the class DigitalModes and an
    overrideable amplitude start and end threshold for audio input.
"""
class DigitalReceiver:
    def __init__(self, digital_mode = DigitalModes.default(), amp_start_threshold = AMP_START_THRESHOLD,
                 amp_end_threshold = AMP_END_THRESHOLD):
        self.digital_mode = digital_mode
        self.amp_start_threshold = amp_start_threshold
        self.amp_end_threshold = amp_end_threshold
        self.unit_time = DigitalModes.getUnitTime(self.digital_mode)
        self.space_tone = DigitalModes.getSpaceTone(self.digital_mode)
        self.mark_tone = DigitalModes.getMarkTone(self.digital_mode)
        waveforms = Waveforms(self.digital_mode)
        self.rx_space = waveforms.getRxSpace()
        self.rx_mark = waveforms.getRxMark()
        self.rx_training = waveforms.getRxTraining()
    
    # Amplifies a chunk of audio for decoding
    def __amplifyChunk(self, chunk: list[int]) -> list[int]:
        amp_chunk = []
        for i in chunk:
            if(i > AMP_DEADZONE):
                amp_chunk.append(32767)
            elif(i < -1 * AMP_DEADZONE):
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
        timeout_iters = round(timeout_seconds * (SAMPLE_RATE / CHUNK_FRAMES))
        pa = pyaudio.PyAudio() # Open an input stream with PortAudio
        stream = pa.open(
            format = FORMAT,
            channels = CHANNELS,
            rate = SAMPLE_RATE,
            input = True,
            frames_per_buffer = CHUNK_FRAMES
        )
        stream.read(CHUNK_FRAMES) # Flush input buffer
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
            block_frames = stream.read(CHUNK_FRAMES)
            chunk_amplitude = self.__avgDeviationBytes(block_frames)
            # Record if we hear a signal
            if(chunk_amplitude > self.amp_start_threshold):
                while(chunk_amplitude > self.amp_end_threshold):
                    # Record until we no longer hear a signal
                    block_frames = stream.read(CHUNK_FRAMES)
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
                fit_devs.append(self.__compareWaveforms(self.rx_training, fit_chunk[i:i+self.unit_time * 2]))
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
        return data[end_training_index::]

    # Convert bits to bytes
    def __bitsToBytes(self, b_data: str) -> bytes:
        int_data = []
        i = 0
        while(i < len(b_data)):
            int_data.append(int(b_data[(i):(i+8)], 2))
            i += 8
        return bytes(int_data)
    
    # Receives data and returns it (or fails)
    def rx(self, timeout: int = -1) -> (bytes, int):
        Log.print(0, "Receiver: Listening...")
        recv_audio = self.__listen(timeout)
        if(recv_audio == b""): # if no data
            Log.print(1, "Receiver: No data.")
            return b"", 0
        recv_bits = self.__decodeBits(recv_audio)
        if(recv_bits == ""): # if no usable data
            Log.print(1, "Receiver: No usable data.")
            return b"", 0
        recv_bits = self.__trimTrainingSeq(recv_bits)
        dec_bits = ECC.decode(recv_bits)
        dec_bytes = self.__bitsToBytes(dec_bits)
        Log.print(0, "Receiver: Done.")
        return dec_bytes

"""
    DigitalTransmitter is a user-defined transmitter class that provides
    functionality for encoding and sending messages.
    It is instantiated with a digital mode from the class DigitalModes and an
    overrideable training sequence time in seconds.
"""
class DigitalTransmitter:
    def __init__(self, digital_mode = DigitalModes.default(), training_seq_time = TRAINING_SEQUENCE_TIME):
        self.digital_mode = digital_mode
        self.ts_cycles = DigitalModes.getTrainingCycles(training_seq_time, self.digital_mode)
        self.unit_time = DigitalModes.getUnitTime(self.digital_mode)
        waveforms = Waveforms(digital_mode = self.digital_mode)
        self.tx_space = waveforms.getTxSpace()
        self.tx_mark = waveforms.GetTxMark()
        self.tx_silence = waveforms.getTxSilence()

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
        Log.print(0, "Transmitter: Sending " + str(len(data)) + " bytes... (ETA: "
                + str(self.estimateTxTime(len(data))) + " sec.)")
        message_bits = self.__bytesToBits(data)
        ecc_bits = ECC.encode(message_bits)
        training_block = self.__getTrainingBlock()
        tx_bits = training_block + ecc_bits
        tx_audio = self.__encodeBits(tx_bits)
        self.__playWaveform(tx_audio)
        Log.print(0, "Transmitter: Done.")
    
    # Estimate transmission time in seconds
    def estimateTxTime(self, length: int) -> float: 
        return (self.ts_cycles * 2 + length * 12) / (SAMPLE_RATE / self.unit_time)
