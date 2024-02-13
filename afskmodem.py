"""
  afskmodem.py
  https://lavajuno.github.io/afskmodem
  Author: Juno Meifert
"""

import struct
import pyaudio
from datetime import datetime
from time import sleep

# Log level (0: Info (Recommended), 1: Warn, 2: Error, 3: None)
LOG_LEVEL = 0

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
    Waveforms provides functions to load waveforms from files and return them 
    as lists of amplitudes, stored as either bytes or ints.
    It is instantiated with a digital mode from the class DigitalModes.
"""
class Waveforms:
    # Generates a single space tone for the given baud rate
    def getSpaceTone(baud_rate: int) -> list[int]:
        if(48000 % baud_rate != 0 or baud_rate % 4 != 0):
            raise Exception("Invalid baud rate.")
        bit_frames: int = 48000 / baud_rate
        res: list[int] = []
        for i in range(int(bit_frames / 2)):
            res.append(32767)
        for i in range(int(bit_frames / 1)):
            res.append(-32768)
        return res

    # Generates a single mark tone for the given baud rate
    def getMarkTone(baud_rate: int) -> list[int]:
        if(48000 % baud_rate != 0 or baud_rate % 4 != 0):
            raise Exception("Invalid baud rate.")
        res: list[int] = Waveforms.getSpaceTone(baud_rate * 2)
        res.extend(Waveforms.getSpaceTone(baud_rate * 2))
        return res

    # Generates a single training cycle for the given baud rate
    def getTrainingCycle(baud_rate: int) -> list[int]:
        res: list[int] = Waveforms.getMarkTone(baud_rate)
        res.extend(Waveforms.getSpaceTone(baud_rate))
        return res
    
    # Gets the mean amplitude of a waveform.
    def getAmplitude(self, frames: list[int]) -> int: 
        sum = 0
        for frame in frames:
            sum += abs(frame)
        return int(sum / len(frames))
    
    # Gets the mean of the differences between two waveforms at each frame
    def getDiff(self, a: list[int], b: list[int]) -> int:
        total: int = 0
        for i in range(len(a)):
            total += abs(a[i] - b[i])
        return int(total / len(a))


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
    
class SoundInput:
    def __init__(self):
        self.__pa: pyaudio = pyaudio.PyAudio()
        self.__stream: pyaudio.Stream = self.__pa.open(
            format = pyaudio.paInt16,
            channels = 1,
            rate = 48000,
            input = True,
            frames_per_buffer = 2048
    )

    def start(self):
        self.__stream.start_stream()

    def stop(self):
        self.__stream.stop_stream()

    def listen(self) -> list[int]:
        frames: bytes = self.__stream.read(2048)
        res: list[int] = []
        for i in range(0, len(frames) - 1, 2):
            s_frame = frames[i:i+2]
            res.append(struct.unpack("<h", s_frame)[0])
        return res

    def close(self):
        self.__stream.close()

class SoundOutput:
    def __init__(self):
        self.__pa: pyaudio = pyaudio.PyAudio()
        self.__stream: pyaudio.Stream = self.__pa.open(
                format = pyaudio.paInt16,
                channels = 1,
                rate = 48000,
                output = True
        )
        self.__stream.start_stream()
    
    def play(self, frames: list[int]):
        
        out_frames: bytearray = []
        for i in range(0, len(frames) - 1, 2):
            out_frames.extend(frames[i].to_bytes(2, 'little', signed=True))
        self.__stream.write(bytes(out_frames))
        

    def close(self):
        self.__stream.stop_stream()
        self.__stream.close()

"""
    DigitalReceiver is a user-defined receiver class that provides functionality 
    for receiving and decoding messages.
    It is instantiated with a digital mode from the class DigitalModes and an
    overrideable amplitude start and end threshold for audio input.
"""
class DigitalReceiver:
    def __init__(self, baud_rate: int = 1200, amp_start_threshold: int = 18000,
                 amp_end_threshold: int = 14000):
        self.__bit_frames: int = 48000 / baud_rate
        self.__amp_start_threshold: int = amp_start_threshold
        self.__amp_end_threshold: int = amp_end_threshold
        self.space_tone: list[int] = Waveforms.getSpaceTone(baud_rate)
        self.mark_tone: list[int] = Waveforms.getMarkTone(baud_rate)
        self.training_cycle: list[int] = Waveforms.getTrainingCycle()
        self.__sound_in: SoundInput = SoundInput()
    
    # Amplifies a received signal
    def __amplify(self, chunk: list[int]) -> list[int]:
        amp_chunk = []
        for i in chunk:
            if(i > 512):
                amp_chunk.append(32767)
            elif(i < -512):
                amp_chunk.append(-32767)
            else:
                amp_chunk.append(0)
        return amp_chunk

    # Records a signal and returns it as a list of frames
    def __listen(self, timeout_frames: int) -> list[int]:
        recorded_frames: list[int] = []
        listened_frames: int = 0
        self.__sound_in.start()
        self.__sound_in.listen(2048) # Discard initial input
        while (listened_frames < timeout_frames):
            frames: list[int] = self.__sound_in.listen()
            if(Waveforms.getAmplitude(frames) > self.__amp_start_threshold):
                recorded_frames.extend(frames)
                break
            listened_frames += 2048
        while (True):
            frames: list[int] = self.__sound_in.listen()
            recorded_frames.extend(frames)
            if(Waveforms.getAmplitude(frames) < self.__amp_end_threshold):
                break
        return recorded_frames

    # Recover the clock from a training sequence
    def __recoverClockIndex(self, frames: list[int]) -> int:
        try:
            if(len(frames) < 4096):
                return -1
            scan_diffs: list[int] = []
            for i in range(4096 - self.__bit_frames * 2): 
                scan_diffs.append(
                    Waveforms.getDiff(self.training_cycle, 
                                      frames[i:i+self.__bit_frames * 2])
                )
            min_diff: int = scan_diffs[0]
            min_index: int = 0
            for i in range(len(scan_diffs)):
                if(scan_diffs[i] < min_diff):
                    min_index = i
                    min_diff = scan_diffs[i]
            return min_index

        except Exception as e:
            # Catch most often an out-of-bounds exception 
            # indicating not enough good data (TODO improve error handling)
            return -1

    # Decide if a sample represents a 1 or 0
    def __decodeBit(self, frames: list[int]) -> str:
        # Amplify received wave to approximate to a square wave
        amp_frames = self.__amplify(frames)
        # Compare to ideal square waves
        mark_diff = Waveforms.getDiff(self.mark_tone, amp_frames)
        space_diff = Waveforms.getDiff(self.space_tone, amp_frames)
        if(mark_diff < space_diff):
            return "1"
        else:
            return "0"

    # Decode bits from an audio sample
    def __decodeBits(self, frames: list[int]) -> str:
            # Recover clock
            i: int = self.__recoverClockIndex(frames)
            if(i == -1): 
                return ""

            # Skip past training sequence
            training_bits: list[int] = [0] * 4
            while(i < len(frames) - self.__bit_frames):
                chunk: list[int] = frames[i:i+self.__bit_frames]
                if(self.__scanTraining(training_bits, self.__decodeBit(chunk))):
                    i += self.__bit_frames
                    break
            
            bits: str = ""
            # Decode and store received bits
            while(i < len(frames) - self.__bit_frames):
                chunk: list[int] = frames[i:i+self.__bit_frames]
                # End decode when no more data is present
                if(Waveforms.getAmplitude(chunk) < self.__amp_end_threshold): 
                    break
                bits += self.__decodeBit(chunk)
                i += self.__bit_frames
            return bits

    # Updates a sliding window of training sequence bits with the given
    # current bit, and returns true if the window matches the training sequence terminator.
    def __scanTraining(self, seq: list[int], current: int):
        for i in range(1, 4):
            seq[i - 1] = seq[i]
        seq[3] = current
        return seq[0] == 1 and seq[1] == 0 and seq[2] == 0 and seq[3] == 0

    # Convert bits to bytes
    def __bitsToBytes(self, bits: str) -> bytes:
        res = []
        i = 0
        while(i < len(bits) - 8):
            res.append(int(bits[(i):(i+8)], 2))
            i += 8
        return bytes(res)
    
    # Receives data and returns it (or fails)
    def rx(self, timeout: int = -1) -> bytes:
        Log.print(0, "Receiver: Listening...")
        recv_audio = self.__listen(timeout)
        if(recv_audio == []): # if no data
            Log.print(1, "Receiver: No data.")
            return b"", 0
        recv_bits = self.__decodeBits(recv_audio)
        if(recv_bits == ""): # if no usable data
            Log.print(1, "Receiver: No usable data.")
            return b"", 0
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

    def __init__(self, baud_rate: int = 1200, training_time: float = 0.5):
        self.__bit_frames: int = int(48000 / baud_rate)
        self.__ts_cycles: int = int(baud_rate * training_time / 2)
        self.__space_tone = Waveforms.getSpaceTone(baud_rate)
        self.__mark_tone = Waveforms.getMarkTone(baud_rate)
        self.__sound_out = SoundOutput()
    
    # Convert bytes to bits
    def __bytesToBits(self, b_in: bytes) -> str:
        bits = ""
        for i in range(len(b_in)):
            bits += '{0:08b}'.format(b_in[i])
        return bits

    # Encode bits to audio
    def __encodeBits(self, bits: str) -> list[int]:
        out_frames: list[int] = []
        # Pad the start with silence
        out_frames += [0] * self.__bit_frames
        # Write out bits as space and mark tones
        for bit in bits:
            if(bit == "0"):
                out_frames += self.__space_tone
            else:
                out_frames += self.__mark_tone
        # Pad the end with silence
        out_frames += [0] * self.__bit_frames
        return out_frames

    # Generate training sequence bits
    def __getTrainingBlock(self) -> str:
        output = "10" * self.__ts_cycles
        output += "1"
        output += "0" * 3
        return output

    # Transmits the given data.
    def tx(self, data: bytes): 
        Log.print(0, "Transmitter: Sending " + str(len(data)) + " bytes...")
        message_bits = self.__bytesToBits(data)
        ecc_bits = ECC.encode(message_bits)
        training_block = self.__getTrainingBlock()
        tx_bits = training_block + ecc_bits
        tx_audio = self.__encodeBits(tx_bits)
        self.__sound_out.play(tx_audio)
        Log.print(0, "Transmitter: Done.")
