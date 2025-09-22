"""
afskmodem.py
https://lavajuno.github.io/afskmodem
Author: Juno Meifert
Modified: 2025-09-21
"""

import logging
import wave

import pyaudio

# Set to True to enable debug logging
DEBUG: bool = False

AUDIO_SAMPLE_RATE: int = 48000
AUDIO_FRAME_BITS: int = 16
AUDIO_FRAME_BITS_SIGNED = AUDIO_FRAME_BITS - 1

_logger = logging.getLogger("afskmodem")
_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
_logger_console_handler = logging.StreamHandler()
_logger_console_handler.setLevel(logging.DEBUG)
_logger_console_handler.setFormatter(
    logging.Formatter("{asctime} {levelname:<8} {name:<24} : {message}", style="{")
)
_logger.addHandler(_logger_console_handler)


class Waveforms:
    """
    Waveforms provides functionality to generate and analyze waveforms.
    """

    @staticmethod
    def get_space_tone(baud_rate: int) -> list[int]:
        """
        Generates a single space tone for the given baud rate
        """
        if AUDIO_SAMPLE_RATE % baud_rate != 0:
            raise ValueError("Invalid baud rate.")
        bit_frames: int = AUDIO_SAMPLE_RATE // baud_rate
        res: list[int] = []
        for i in range(bit_frames // 2):
            res.append((2**AUDIO_FRAME_BITS_SIGNED) - 1)
        for i in range(bit_frames // 2):
            res.append(-(2**AUDIO_FRAME_BITS_SIGNED))
        return res

    @staticmethod
    def get_mark_tone(baud_rate: int) -> list[int]:
        """
        Generates a single mark tone for the given baud rate
        """
        if AUDIO_SAMPLE_RATE % baud_rate != 0:
            raise ValueError("Invalid baud rate.")
        res = Waveforms.get_space_tone(baud_rate * 2)
        res.extend(Waveforms.get_space_tone(baud_rate * 2))
        return res

    @staticmethod
    def get_training_cycle(baud_rate: int) -> list[int]:
        """
        Generates a single training cycle for the given baud rate
        """
        res: list[int] = Waveforms.get_mark_tone(baud_rate)
        res.extend(Waveforms.get_space_tone(baud_rate))
        return res

    @staticmethod
    def getAmplitude(frames: list[int]) -> int:
        """
        Gets the mean amplitude of a waveform
        """
        sum = 0
        for frame in frames:
            sum += abs(frame)
        return int(sum / len(frames))

    @staticmethod
    def get_diff(a: list[int], b: list[int]) -> int:
        """
        Gets the mean of the differences between two waveforms at each frame
        """
        if len(a) != len(b):
            raise Exception("Comparing two waveforms of different lengths.")
        total: int = 0
        for i in range(len(a)):
            total += abs(a[i] - b[i])
        return int(total / len(a))


class ECC:
    """
    ECC provides functionality for encoding and decoding data with Hamming(4,3),
    correcting bit errors as it decodes.
    """

    __M_GENERATOR: list[list[int]] = [
        [1, 1, 0, 1],
        [1, 0, 1, 1],
        [1, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]

    __M_PARITY: list[list[int]] = [
        [1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 1],
    ]

    @staticmethod
    def __multiply(a: list[list[int]], b: list[int]) -> list[int]:
        """
        Multiplies a matrix and vector modulo 2
        """
        result: list[int] = [0] * len(a)
        for i in range(0, len(a)):
            for j in range(0, len(b)):
                result[i] += a[i][j] * b[j]
            result[i] %= 2
        return result

    @classmethod
    def __encode_nibble(cls, data: list[int]) -> list[int]:
        """
        Encodes 4 data bits
        """
        return cls.__multiply(cls.__M_GENERATOR, data)

    @classmethod
    def __decode_nibble(cls, data: list[int]) -> list[int]:
        """
        Decodes 4 data bits
        """
        syn: list[int] = cls.__multiply(cls.__M_PARITY, data)
        error_pos: int = syn[2] * 4 + syn[1] * 2 + syn[0]
        res: list[int] = data
        if error_pos != 0:
            res[error_pos - 1] = 0 if res[error_pos - 1] == 1 else 1
        return [res[2], res[4], res[5], res[6]]

    @classmethod
    def decode(cls, bits: str) -> str:
        """
        Corrects errors and decodes data. Returns decoded bits.
        """
        dec_bits = ""
        for i in range(0, len(bits) - 6, 7):
            raw_bits: list[int] = []
            for j in bits[i : i + 7]:
                raw_bits.append(0 if j == "0" else 1)
            dec_nibble = cls.__decode_nibble(raw_bits)
            for j in dec_nibble:
                dec_bits += "0" if j == 0 else "1"
        return dec_bits

    @classmethod
    def encode(cls, bits: str) -> str:
        """
        Encodes data by inserting parity bits
        """
        enc_bits = ""
        for i in range(0, len(bits) - 3, 4):
            raw_bits: list[int] = []
            for j in bits[i : i + 4]:
                raw_bits.append(0 if j == "0" else 1)
            enc_nibble = ECC.__encode_nibble(raw_bits)
            for j in enc_nibble:
                enc_bits += "0" if j == 0 else "1"
        return enc_bits


class SoundInput:
    """
    SoundInput provides functionality for reading from the default audio
    input device.
    """

    def __init__(self):
        self.__pa: pyaudio.PyAudio = pyaudio.PyAudio()
        self.__stream: pyaudio.Stream = self.__pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=2048,
        )

    def start(self) -> None:
        """
        Starts the input stream
        """
        self.__stream.start_stream()

    def stop(self) -> None:
        """
        Stops the input stream
        """
        self.__stream.stop_stream()

    @staticmethod
    def __convert_frames(frames: bytes) -> list[int]:
        """
        Converts frames from bytes to a list of integers
        """
        res: list[int] = []
        for i in range(0, len(frames) - 1, 2):
            res.append(int.from_bytes(frames[i : i + 2], "little", signed=True))
        return res

    def listen(self) -> list[int]:
        """
        Listens to input stream and returns a list of frames
        """
        return self.__convert_frames(self.__stream.read(2048))

    @classmethod
    def load_from_file(cls, filename: str) -> list[int]:
        """
        Loads a wav file and returns a list of frames
        Input file must be 48khz 16-bit mono
        """
        with wave.open(filename, "rb") as f:
            return cls.__convert_frames(f.readframes(f.getnframes()))

    # Closes the input stream
    def close(self) -> None:
        self.__stream.close()


class SoundOutput:
    """
    SoundOutput provides functionality for writing to the default audio
    output device.
    """

    def __init__(self):
        self.__pa: pyaudio.PyAudio = pyaudio.PyAudio()
        self.__stream: pyaudio.Stream = self.__pa.open(
            format=pyaudio.paInt16, channels=1, rate=AUDIO_SAMPLE_RATE, output=True
        )
        self.__stream.start_stream()

    @staticmethod
    def __convert_frames(frames: list[int]) -> bytes:
        """
        Converts frames from a list of integers to bytes
        """
        res = bytearray()
        for i in range(0, len(frames) - 1, 2):
            frame = frames[i].to_bytes(2, "little", signed=True)
            res.extend(frame * 2)
        return bytes(res)

    def play(self, frames: list[int]):
        """
        Writes frames to the output stream and blocks
        """
        self.__stream.write(
            self.__convert_frames(frames), len(frames), exception_on_underflow=False
        )

    @classmethod
    def write_to_file(cls, filename: str, frames: list[int]):
        """
        Writes frames to a wav file
        Output file will be 16-bit mono. Sample rate is specified with
        AUDIO_FRAME_BITS.
        """
        with wave.open(filename, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(AUDIO_SAMPLE_RATE)
            f.writeframes(cls.__convert_frames(frames))

    def close(self):
        """
        Closes the output stream
        """
        self.__stream.stop_stream()
        self.__stream.close()


class Receiver:
    """
    Receiver manages a line to the default audio input device
    and allows you to receive data over it.
    """

    def __init__(
        self,
        baud_rate: int = 1200,
        amp_start_threshold: int = 18000,
        amp_end_threshold: int = 14000,
    ):
        self.__bit_frames: int = int(AUDIO_SAMPLE_RATE / baud_rate)
        self.__amp_start_threshold: int = amp_start_threshold
        self.__amp_end_threshold: int = amp_end_threshold
        self.__space_tone: list[int] = Waveforms.get_space_tone(baud_rate)
        self.__mark_tone: list[int] = Waveforms.get_mark_tone(baud_rate)
        self.__training_cycle: list[int] = Waveforms.get_training_cycle(baud_rate)
        self.__sound_in: SoundInput = SoundInput()

    def __amplify(self, chunk: list[int]) -> list[int]:
        """
        Amplifies a received signal
        """
        res: list[int] = []
        for i in chunk:
            if i > 512:
                res.append((2**AUDIO_FRAME_BITS_SIGNED) - 1)
            elif i < -512:
                res.append(-(2**AUDIO_FRAME_BITS_SIGNED))
            else:
                res.append(0)
        return res

    def __listen(self, timeout_frames: int) -> list[int]:
        """
        Records a signal and returns it as a list of frames
        """
        recorded_frames: list[int] = []
        listened_frames: int = 0
        self.__sound_in.start()
        self.__sound_in.listen()  # Discard initial input
        while listened_frames < timeout_frames:
            frames: list[int] = self.__sound_in.listen()
            if Waveforms.getAmplitude(frames) > self.__amp_start_threshold:
                _logger.debug("rx: Recording started")
                recorded_frames.extend(frames)
                break
            listened_frames += 2048
        if listened_frames >= timeout_frames:
            return []
        while True:
            frames: list[int] = self.__sound_in.listen()
            recorded_frames.extend(frames)
            if Waveforms.getAmplitude(frames) < self.__amp_end_threshold:
                _logger.debug("rx: Recording finished")
                break
        return recorded_frames

    def __recover_clock_index(self, frames: list[int]) -> int:
        """
        Recover the clock from a training sequence
        """
        if len(frames) < 4096:
            _logger.warning("rx: Failed to recover clock from received signal.")
            return -1
        scan_diffs: list[int] = []
        for i in range(4096 - self.__bit_frames * 2):
            scan_diffs.append(
                Waveforms.get_diff(
                    self.__training_cycle, frames[i : i + self.__bit_frames * 2]
                )
            )
        min_diff: int = scan_diffs[0]
        min_index: int = 0
        for i in range(len(scan_diffs)):
            if scan_diffs[i] < min_diff:
                min_index = i
                min_diff = scan_diffs[i]
        _logger.debug("rx: Recovered clock. (frame " + str(min_index) + ")")
        return min_index

    def __decode_bit(self, frames: list[int]) -> str:
        """
        Decode a single bit from a list of frames
        """
        # Amplify received wave to approximate to a square wave
        amp_frames = self.__amplify(frames)
        # Compare to ideal square waves
        mark_diff = Waveforms.get_diff(self.__mark_tone, amp_frames)
        space_diff = Waveforms.get_diff(self.__space_tone, amp_frames)
        if mark_diff < space_diff:
            return "1"
        else:
            return "0"

    def __decode_bits(self, frames: list[int]) -> str:
        """
        Decode bits from a recorded signal
        """
        # Recover clock
        i: int = self.__recover_clock_index(frames)
        if i == -1:
            return ""

        # Skip past training sequence
        training_bits: list[int] = [0] * 4
        while i < len(frames) - self.__bit_frames:
            chunk: list[int] = frames[i : i + self.__bit_frames]
            i += self.__bit_frames
            if self.__scan_training(training_bits, self.__decode_bit(chunk)):
                break

        _logger.debug("rx: Training sequence terminated on frame " + str(i))

        bits: str = ""
        # Decode and store received bits
        while i < len(frames) - self.__bit_frames:
            chunk: list[int] = frames[i : i + self.__bit_frames]
            # End decode when no more data is present
            if Waveforms.getAmplitude(chunk) < self.__amp_end_threshold:
                break
            bits += self.__decode_bit(chunk)
            i += self.__bit_frames

        _logger.debug("rx: Decoded " + str(len(bits)) + " bits. (including ECC)")
        return bits

    def __scan_training(self, seq: list[int], current: str):
        """
        Updates a sliding window of training sequence bits with the given
        current bit, and returns true if the window matches the training
        sequence terminator.
        """
        for i in range(1, 4):
            seq[i - 1] = seq[i]
        seq[3] = 0 if current == "0" else 1
        return seq[0] == 1 and seq[1] == 0 and seq[2] == 0 and seq[3] == 0

    def __bits_to_bytes(self, bits: str) -> bytes:
        """
        Convert bits to bytes
        """
        res = []
        i = 0
        while i <= len(bits) - 8:
            res.append(int(bits[(i) : (i + 8)], 2))
            i += 8
        return bytes(res)

    def receive(self, timeout: float, string: bool = True) -> bytes | str:
        """
        Receives signal, decodes it, then returns it (or fails)
        """
        _logger.info("rx: Listening...")
        recv_audio = self.__listen(int(timeout * 48000))
        if recv_audio == []:
            _logger.warning("rx: Timed out.")
            return b""
        recv_bits = self.__decode_bits(recv_audio)
        if recv_bits == "":
            _logger.warning("rx: No data.")
            return b""
        dec_bits = ECC.decode(recv_bits)
        dec_bytes = self.__bits_to_bytes(dec_bits)
        _logger.debug("rx: Decoded " + str(len(dec_bytes)) + " bytes.")
        if string:
            return dec_bytes.decode("utf-8")
        return dec_bytes

    def load(self, filename: str, string: bool = True) -> bytes | str:
        """
        Reads signal from a file, decodes it, then returns it (or fails)
        """
        recv_bits = self.__decode_bits(SoundInput.load_from_file(filename))
        if recv_bits == "":
            _logger.warning("rx: No data.")
            return b""
        dec_bits = ECC.decode(recv_bits)
        dec_bytes = self.__bits_to_bytes(dec_bits)
        _logger.debug("rx: Decoded " + str(len(dec_bytes)) + " bytes.")
        if string:
            return dec_bytes.decode("utf-8")
        return dec_bytes


class Transmitter:
    """
    Transmitter manages a line to the default audio output device
    and allows you to send data over it.
    """

    def __init__(self, baud_rate: int = 1200, training_time: float = 0.5):
        self.__ts_cycles: int = int(baud_rate * training_time / 2)
        self.__space_tone = Waveforms.get_space_tone(baud_rate)
        self.__mark_tone = Waveforms.get_mark_tone(baud_rate)
        self.__training_cycle = Waveforms.get_training_cycle(baud_rate)
        self.__sound_out = SoundOutput()

    # Convert bytes to bits
    def __bytes_to_bits(self, b_in: bytes) -> str:
        bits = ""
        for i in range(len(b_in)):
            bits += "{0:08b}".format(b_in[i])
        return bits

    def __get_frames(self, data: bytes):
        frames: list[int] = []
        message_bits = self.__bytes_to_bits(data)
        ecc_bits = ECC.encode(message_bits)
        # Training sequence
        for i in range(self.__ts_cycles):
            frames.extend(self.__training_cycle)
        # Training sequence terminator
        frames.extend(self.__mark_tone)
        for i in range(3):
            frames.extend(self.__space_tone)
        for i in ecc_bits:
            if i == "0":
                frames.extend(self.__space_tone)
            else:
                frames.extend(self.__mark_tone)
        frames.extend([0] * (AUDIO_SAMPLE_RATE // 10))
        return frames

    def transmit(self, data: str | bytes):
        """
        Transmits the given data.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        _logger.info("tx: Transmitting " + str(len(data)) + " bytes...")
        frames = self.__get_frames(data)
        _logger.info("tx: Transmitting " + str(len(frames)) + " frames...")
        self.__sound_out.play(frames)

    def save(self, data: str | bytes, filename: str):
        """
        Transmits the given data, saving the resulting audio to a .wav file.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        SoundOutput.write_to_file(filename, self.__get_frames(data))
