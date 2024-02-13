"""
  afskmodem.py
  https://lavajuno.github.io/afskmodem
  Author: Juno Meifert
"""

import pyaudio
from datetime import datetime

# Log level (0: Info (Recommended), 1: Warn, 2: Error, 3: None)
LOG_LEVEL = 0

"""
    Log provides simple logging functionality.
"""
class Log:
    def __init__(self, class_name: str):
        self.__class_name = class_name

    # Prints a log event
    def __print(self, level: int, message: str):
        if(level >= LOG_LEVEL):
            output = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output += " (afskmodem) "
            match level:
                case 1:
                    output += "[ INFO ]  "
                case 2:
                    output += "[ WARN ]  "
                case 3:
                    output += "[ ERROR ] "
                case 4:
                    output += "[ FATAL ] "
                case _:
                    output += "[ DEBUG ] "
            output += self.__class_name.ljust(20)
            output += ": "
            output += message
            print(output)

    # Prints a log event with severity DEBUG
    def debug(self, message: str):
        self.__print(0, message)

    # Prints a log event with severity INFO
    def info(self, message: str):
        self.__print(1, message)
    
    # Prints a log event with severity WARN
    def warn(self, message: str):
        self.__print(2, message)

    # Prints a log event with severity ERROR
    def error(self, message: str):
        self.__print(3, message)

    # Prints a log event with severity FATAL
    def fatal(self, message: str):
        self.__print(4, message)

"""
    Waveforms provides functionality to generate and analyze waveforms.
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
        for i in range(int(bit_frames / 2)):
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
    
    # Gets the mean amplitude of a waveform
    def getAmplitude(frames: list[int]) -> int: 
        sum = 0
        for frame in frames:
            sum += abs(frame)
        return int(sum / len(frames))
    
    # Gets the mean of the differences between two waveforms at each frame
    def getDiff(a: list[int], b: list[int]) -> int:
        if(len(a) != len(b)):
            raise Exception("Comparing two waveforms of different lengths.")
        total: int = 0
        for i in range(len(a)):
            total += abs(a[i] - b[i])
        return int(total / len(a))


"""
    ECC provides functionality for encoding and decoding data with Hamming(4,3),
    correcting bit errors as it decodes.
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
    SoundInput provides functionality for reading from the default audio 
    input device.
"""
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

    # Starts the input stream
    def start(self):
        self.__stream.start_stream()

    # Stops the input stream
    def stop(self):
        self.__stream.stop_stream()
    
    # Listens to input stream and returns a list of frames
    def listen(self) -> list[int]:
        frames: bytes = self.__stream.read(2048)
        res: list[int] = []
        for i in range(0, len(frames) - 1, 2):
            res.append(int.from_bytes(frames[i:i+2], "little", signed=True))
        return res

    # Closes the input stream
    def close(self):
        self.__stream.close()

"""
    SoundOutput provides functionality for writing to the default audio
    output device.
"""
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
    
    # Writes frames to the output stream and blocks
    def play(self, frames: list[int]):
        out_frames: bytearray = []
        for i in range(0, len(frames) - 1, 2):
            frame = frames[i].to_bytes(2, 'little', signed=True)
            out_frames.extend(frame * 2)
        self.__stream.write(bytes(out_frames), len(frames),
                            exception_on_underflow=False)

    # Closes the output stream
    def close(self):
        self.__stream.stop_stream()
        self.__stream.close()

"""
    Receiver manages a line to the default audio input device
    and allows you to receive data over it.
"""
class Receiver:
    def __init__(self, baud_rate: int = 1200, amp_start_threshold: int = 18000,
                 amp_end_threshold: int = 14000):
        self.__bit_frames: int = int(48000 / baud_rate)
        self.__amp_start_threshold: int = amp_start_threshold
        self.__amp_end_threshold: int = amp_end_threshold
        self.__space_tone: list[int] = Waveforms.getSpaceTone(baud_rate)
        self.__mark_tone: list[int] = Waveforms.getMarkTone(baud_rate)
        self.__training_cycle: list[int] = Waveforms.getTrainingCycle(baud_rate)
        self.__sound_in: SoundInput = SoundInput()
        self.__log = Log("Receiver")
    
    # Amplifies a received signal
    def __amplify(self, chunk: list[int]) -> list[int]:
        res: list[int] = []
        for i in chunk:
            if(i > 512):
                res.append(32767)
            elif(i < -512):
                res.append(-32768)
            else:
                res.append(0)
        return res

    # Records a signal and returns it as a list of frames
    def __listen(self, timeout_frames: int) -> list[int]:
        recorded_frames: list[int] = []
        listened_frames: int = 0
        self.__sound_in.start()
        self.__sound_in.listen() # Discard initial input
        while (listened_frames < timeout_frames):
            frames: list[int] = self.__sound_in.listen()
            if(Waveforms.getAmplitude(frames) > self.__amp_start_threshold):
                self.__log.debug("Recording started")
                recorded_frames.extend(frames)
                break
            listened_frames += 2048
        if(listened_frames >= timeout_frames):
            return []
        while (True):
            frames: list[int] = self.__sound_in.listen()
            recorded_frames.extend(frames)
            if(Waveforms.getAmplitude(frames) < self.__amp_end_threshold):
                self.__log.debug("Recording finished")
                break
        return recorded_frames

    # Recover the clock from a training sequence
    def __recoverClockIndex(self, frames: list[int]) -> int:
        if(len(frames) < 4096):
            self.__log.warn("Failed to recover clock from received signal.")
            return -1
        scan_diffs: list[int] = []
        for i in range(4096 - self.__bit_frames * 2):
            scan_diffs.append(
                Waveforms.getDiff(self.__training_cycle, 
                                    frames[i:i+self.__bit_frames * 2])
            )
        min_diff: int = scan_diffs[0]
        min_index: int = 0
        for i in range(len(scan_diffs)):
            if(scan_diffs[i] < min_diff):
                min_index = i
                min_diff = scan_diffs[i]
        self.__log.debug("Recovered clock. (frame " + str(min_index) + ")")
        return min_index

    # Decode a single bit from a list of frames
    def __decodeBit(self, frames: list[int]) -> str:
        # Amplify received wave to approximate to a square wave
        amp_frames = self.__amplify(frames)
        # Compare to ideal square waves
        mark_diff = Waveforms.getDiff(self.__mark_tone, amp_frames)
        space_diff = Waveforms.getDiff(self.__space_tone, amp_frames)
        if(mark_diff < space_diff):
            return "1"
        else:
            return "0"

    # Decode bits from a recorded signal
    def __decodeBits(self, frames: list[int]) -> str:
            # Recover clock
            i: int = self.__recoverClockIndex(frames)
            if(i == -1):
                return ""

            # Skip past training sequence
            training_bits: list[int] = [0] * 4
            while(i < len(frames) - self.__bit_frames):
                chunk: list[int] = frames[i:i+self.__bit_frames]
                i += self.__bit_frames
                if(self.__scanTraining(training_bits, self.__decodeBit(chunk))):
                    break
            
            self.__log.debug("Training sequence terminated on frame " + str(i))
            
            bits: str = ""
            # Decode and store received bits
            while(i < len(frames) - self.__bit_frames):
                chunk: list[int] = frames[i:i+self.__bit_frames]
                # End decode when no more data is present
                if(Waveforms.getAmplitude(chunk) < self.__amp_end_threshold): 
                    break
                bits += self.__decodeBit(chunk)
                i += self.__bit_frames
            
            self.__log.debug("Decoded " + str(len(bits)) + " bits. (including ECC)")
            return bits

    # Updates a sliding window of training sequence bits with the given
    # current bit, and returns true if the window matches the training 
    # sequence terminator.
    def __scanTraining(self, seq: list[int], current: str):
        for i in range(1, 4):
            seq[i - 1] = seq[i]
        seq[3] = 0 if current == "0" else 1
        return seq[0] == 1 and seq[1] == 0 and seq[2] == 0 and seq[3] == 0

    # Convert bits to bytes
    def __bitsToBytes(self, bits: str) -> bytes:
        res = []
        i = 0
        while(i <= len(bits) - 8):
            res.append(int(bits[(i):(i+8)], 2))
            i += 8
        return bytes(res)
    
    # Receives data and returns it (or fails)
    def receive(self, timeout: float) -> bytes:
        self.__log.info("Listening...")
        recv_audio = self.__listen(int(timeout * 48000))
        if(recv_audio == []):
            self.__log.warn("Timed out.")
            return b""
        recv_bits = self.__decodeBits(recv_audio)
        if(recv_bits == ""):
            self.__log.warn("No data.")
            return b""
        dec_bits = ECC.decode(recv_bits)
        dec_bytes = self.__bitsToBytes(dec_bits)
        self.__log.debug("Decoded " + str(len(dec_bytes)) + " bytes.")
        return dec_bytes

"""
    Transmitter manages a line to the default audio output device
    and allows you to send data over it.
"""
class Transmitter:
    def __init__(self, baud_rate: int = 1200, training_time: float = 0.5):
        self.__ts_cycles: int = int(baud_rate * training_time / 2)
        self.__space_tone = Waveforms.getSpaceTone(baud_rate)
        self.__mark_tone = Waveforms.getMarkTone(baud_rate)
        self.__training_cycle = Waveforms.getTrainingCycle(baud_rate)
        self.__sound_out = SoundOutput()
        self.__log = Log("Transmitter") 
    
    # Convert bytes to bits
    def __bytesToBits(self, b_in: bytes) -> str:
        bits = ""
        for i in range(len(b_in)):
            bits += '{0:08b}'.format(b_in[i])
        return bits

    # Transmits the given data.
    def transmit(self, data: bytes): 
        self.__log.info("Transmitting " + str(len(data)) + " bytes...")
        frames: list[int] = []
        message_bits = self.__bytesToBits(data)
        ecc_bits = ECC.encode(message_bits)
        # Training sequence
        for i in range(self.__ts_cycles):
            frames.extend(self.__training_cycle)
        # Training sequence terminator
        frames.extend(self.__mark_tone)
        for i in range(3):
            frames.extend(self.__space_tone)
        for i in ecc_bits:
            if(i == "0"):
                frames.extend(self.__space_tone)
            else:
                frames.extend(self.__mark_tone)
        frames.extend([0] * 4800)
        self.__log.info("Transmitting " + str(len(data)) + " frames...")
        self.__sound_out.play(frames)
