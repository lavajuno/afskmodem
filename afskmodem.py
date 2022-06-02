"""
x----------------------------------------------x
| AFSKmodem - Simple, reliable digital radio.  |
| https://jmeifert.github.io/afskmodem         |
x----------------------------------------------x
"""
import wave
import struct
import pyaudio
from time import sleep

################################################################################ PROGRAM DEFAULTS

# USER-CONFIGURABLE PARAMETERS: Although these should work fine as-is, fine-tuning them will not affect functionality.
#
# Training sequence time in seconds (0.2-1.0, Default 0.6)
TRAINING_SEQUENCE_TIME = 0.6
#
# Chunk amplitude at which decoding starts (0-32768, Default 18000 [-5.2 dBfs])
AMPLITUDE_START_THRESHOLD = 18000
#
# Chunk amplitude at which decoding stops (0-32768, Default 14000 [-7.4 dBfs])
AMPLITUDE_END_THRESHOLD = 14000
#
# Amplifier function deadzone (0-32768, Default 128 [-48.2 dBfs])
AMPLIFIER_DEADZONE = 128
#
# Frames per buffer for audio input (1024-4096, Default 2048 [0.043s]) - Smaller blocks increase CPU usage but decrease latency
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
# Frames to scan for clock recovery (Should scan at least two full blocks in,
# but no more than a portion of the length of the training sequence.)
CLOCK_SCAN_WIDTH = 2 * INPUT_FRAMES_PER_BLOCK
#
# Directory where ideal waves are stored
IDEAL_WAVES_DIR = "data/ideal_waves/"

################################################################################ DIGITAL MODULATION TYPES
class DigitalModulationTypes:
    def afsk300() -> str: # Audio Frequency-Shift Keying (300 baud)
        return "afsk300"
    def afsk600() -> str: # Audio Frequency-Shift Keying (600 baud)
        return "afsk600"
    def afsk1200() -> str: # Audio Frequency-Shift Keying (1200 baud)
        return "afsk1200"
    def afsk2400() -> str: # Audio Frequency-Shift Keying (2400 baud)
        return "afsk2400"
    def afsk6000() -> str: # Audio Frequency-Shift Keying (6000 baud)
        return "afsk6000"
    def default() -> str: # Default (AFSK1200)
        return "afsk1200"
    
    # Unit time in samples
    def get_unit_time(digital_modulation_type: str) -> int:
        if(digital_modulation_type == "afsk300"):
            return int(SAMPLE_RATE / 300)
        elif(digital_modulation_type == "afsk600"):
            return int(SAMPLE_RATE / 600)
        elif(digital_modulation_type == "afsk1200"):
            return int(SAMPLE_RATE / 1200)
        elif(digital_modulation_type == "afsk2400"):
            return int(SAMPLE_RATE / 2400)
        elif(digital_modulation_type == "afsk6000"):
            return int(SAMPLE_RATE / 6000)
        else: # default
            return int(SAMPLE_RATE / 1200)

    # Training sequence oscillations for specified time
    def get_ts_oscillations(sequence_time: int, digital_modulation_type: str) -> int:
        if(digital_modulation_type == "afsk300"):
            return int(300 * sequence_time / 2)
        elif(digital_modulation_type == "afsk600"):
            return int(600 * sequence_time / 2)
        elif(digital_modulation_type == "afsk1200"):
            return int(1200 * sequence_time / 2)
        elif(digital_modulation_type == "afsk2400"):
            return int(2400 * sequence_time / 2)
        elif(digital_modulation_type == "afsk6000"):
            return int(6000 * sequence_time / 2)
        else: # default
            return int(1200 * sequence_time / 2)
    
    # Get the frequency of the space tone for a given type
    def get_space_tone(digital_modulation_type: str) -> int:
        if(digital_modulation_type == "afsk300"):
            return 300
        elif(digital_modulation_type == "afsk600"):
            return 600
        elif(digital_modulation_type == "afsk1200"):
            return 1200
        elif(digital_modulation_type == "afsk2400"):
            return 2400
        elif(digital_modulation_type == "afsk6000"):
            return 6000
        else: # default
            return 1200

    # Get the frequency of the mark tone for a given type
    def get_mark_tone(digital_modulation_type: str) -> int:
        if(digital_modulation_type == "afsk300"):
            return 600
        elif(digital_modulation_type == "afsk600"):
            return 1200
        elif(digital_modulation_type == "afsk1200"):
            return 2400
        elif(digital_modulation_type == "afsk2400"):
            return 4800
        elif(digital_modulation_type == "afsk6000"):
            return 12000
        else: # default
            return 2400

################################################################################ IDEAL WAVES
class IdealWaves: # Ideal waves for TX and RX
    def __init__(self, digital_modulation_type = DigitalModulationTypes.default()):
        self.digital_modulation_type = digital_modulation_type

    # Load wav data to int array
    def __load_wav_data(self, filename: str) -> list:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            expFrames = []
            for i in range(0, nFrames):
                sFrame = f.readframes(1)
                expFrames.append(struct.unpack("<h", sFrame)[0])
            return expFrames

    # Load wav data to bytes
    def __load_raw_wav_data(self, filename: str) -> bytes:
        with wave.open(filename, "r") as f:
            nFrames = f.getnframes()
            return f.readframes(nFrames)
    
    # Silence (20ms) to pad output with for TX
    def get_tx_silence(self) -> bytes: 
        return self.__load_raw_wav_data(IDEAL_WAVES_DIR + "_.wav")
    
    # Space tone as bytes for TX
    def get_tx_space(self) -> bytes: 
        return self.__load_raw_wav_data(IDEAL_WAVES_DIR + self.digital_modulation_type + "/0.wav")
    
    # Mark tone as bytes for TX
    def get_tx_mark(self) -> bytes: 
        return self.__load_raw_wav_data(IDEAL_WAVES_DIR + self.digital_modulation_type + "/1.wav")
    
    # Space tone as int array for RX
    def get_rx_space(self) -> list: 
        return self.__load_wav_data(IDEAL_WAVES_DIR + self.digital_modulation_type + "/0.wav")
    
    # Mark tone as int array for RX
    def get_rx_mark(self) -> list: 
        return self.__load_wav_data(IDEAL_WAVES_DIR + self.digital_modulation_type + "/1.wav")
    
    # Ideal training sequence oscillation for RX clock recovery
    def get_rx_training(self) -> list: 
        return self.get_rx_mark() + self.get_rx_space()

################################################################################ HAMMING ECC
class Hamming:
    # Each instance of Hamming keeps track of the errors it corrects. 
    # An instance of Hamming is created for each DigitalTransmitter or DigitalReceiver instance.
    def __init__(self): 
        self.r = 4
        self.error_count = 0

    def reset_error_count(self): # Reset error count to 0
        self.error_count = 0
    
    def get_error_count(self) -> int: # Get error count
        return self.error_count
    
    def __increment_error_count(self): # Increment error count
        self.error_count += 1
    
    # Pad the positions of parity bits with 0
    def __pad_parity_bits(self, data: str) -> str:
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
    def __set_parity_bits(self, data: str) -> str:
        n = len(data)
        for i in range(self.r):
            p = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    p = p ^ int(data[-1 * j])
            data = data[:n-(2**i)] + str(p) + data[n-(2**i)+1:]
        return data

    # Find an error (if it exists)
    def __get_error_index(self, data: str) -> int:
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
    def __trim_parity_bits(self, data: str) -> str:
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
    def __correct_errors(self, data: str) -> str:
        error_pos = self.__get_error_index(data)
        if(error_pos == len(data)):
            return data
        else:
            self.__increment_error_count()
            data_list = list(data)
            if(data_list[error_pos] == "0"):
                data_list[error_pos] = "1"
            else:
                data_list[error_pos] = "0"
            data = "".join(data_list)
        return data

    # Single function handling generating Hamming code. Returns a tuple with the 
    # result bit string and the number of redundant bits.
    def encode(self, data: str) -> str:
        padded_data = self.__pad_parity_bits(data)
        parity_data = self.__set_parity_bits(padded_data)
        return(parity_data)

    # Single function handling correcting and getting useful data from Hamming
    # code. Returns the data payload.
    def decode(self, data: str) -> str:
        corrected_data = self.__correct_errors(data)
        output_data = self.__trim_parity_bits(corrected_data)
        return(output_data)

################################################################################ RX TOOLS
class DigitalReceiver:
    def __init__(self,
    digital_modulation_type = DigitalModulationTypes.default(),    
    amp_start_threshold = AMPLITUDE_START_THRESHOLD,
    amp_end_threshold = AMPLITUDE_END_THRESHOLD,
    amp_deadzone = AMPLIFIER_DEADZONE):
        self.digital_modulation_type = digital_modulation_type
        self.amp_start_threshold = amp_start_threshold
        self.amp_end_threshold = amp_end_threshold
        self.amp_deadzone = amp_deadzone
        self.unit_time = DigitalModulationTypes.get_unit_time(self.digital_modulation_type)
        self.space_tone = DigitalModulationTypes.get_space_tone(self.digital_modulation_type)
        self.mark_tone = DigitalModulationTypes.get_mark_tone(self.digital_modulation_type)
        ideal_waves = IdealWaves(digital_modulation_type = self.digital_modulation_type)
        self.rx_space = ideal_waves.get_rx_space()
        self.rx_mark = ideal_waves.get_rx_mark()
        self.rx_training = ideal_waves.get_rx_training()
        self.ecc = Hamming()
    
    # Load raw wav data from file
    def __load_raw_wav_data(self, filename: str) -> bytes:
        with wave.open(filename, "r") as f:
            nframes = f.getnframes()
            return f.readframes(nframes)
    
    # From sine to square
    def __amplify_chunk(self, chunk: list) -> list:
        amp_chunk = []
        for i in chunk:
            if(i > self.amp_deadzone):
                amp_chunk.append(32767)
            elif(i < -1 * self.amp_deadzone):
                amp_chunk.append(-32767)
            else:
                amp_chunk.append(0)
        return amp_chunk

    # Average deviation from bytes
    def __avg_deviation_bytes(self, frames: bytes) -> int:
        s_frames = []
        for i in range(len(frames) - 1): 
            s_frame = frames[i:i+2]
            s_frames.append(abs(struct.unpack("<h", s_frame)[0]))
            i += 2
        return int(sum(s_frames) / len(s_frames))

    # Auto-record and return frames
    def __auto__record(self, timeout_seconds=-1) -> bytes:
        timeout_iters = round(timeout_seconds * (SAMPLE_RATE/INPUT_FRAMES_PER_BLOCK))
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
            block_frames = stream.read(INPUT_FRAMES_PER_BLOCK) # Record and sample
            chunk_amplitude = self.__avg_deviation_bytes(block_frames)
            if(chunk_amplitude > self.amp_start_threshold): # Record and return
                while(chunk_amplitude > self.amp_end_threshold):
                    block_frames = stream.read(INPUT_FRAMES_PER_BLOCK)
                    recorded_frames.append(block_frames)
                    chunk_amplitude = self.__avg_deviation_bytes(block_frames)
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return b''.join(recorded_frames)

    # Unsigned average deviation from audio stored as ints
    def __avg_deviation_array(self, chunk: list) -> int: 
        frame_sum = 0
        for frame in chunk:
            frame_sum += abs(frame)
        return int(frame_sum / len(chunk))

    # Find the difference between an ideal wave and a received wave
    def __compare_samples(self, ideal_sample: list, given_sample: list) -> int: 
        differences = []
        for i in range(len(ideal_sample)):
            differences.append(abs(ideal_sample[i] - given_sample[i]))
        return int(sum(differences) / len(differences))

    # Recover the clock from a chunk of audio by scanning the training sequence
    def __recover_clock_index(self, chunk: list) -> int:
        try:
            fit_chunk = self.__amplify_chunk(chunk[0:CLOCK_SCAN_WIDTH]) 
            fit_devs = []
            # Create an array of deviations
            for i in range(len(fit_chunk) - self.unit_time * 2 - 1): 
                fit_devs.append(self.__compare_samples(self.rx_training, fit_chunk[i:i+self.unit_time * 2]))
            # Optimize the error for the best start sample index
            start_index = fit_devs.index(min(fit_devs))
            return start_index

        except Exception as e:
            # Catch most often an out-of-bounds exception indicating not enough good data
            return -1

    # Check if a chunk's value is 1 or 0 based on its similarity to ideal waves.
    def __get_bit_value(self, chunk: list) -> str:
        # Amplify received wave to approximate to a square wave
        decChunk = self.__amplify_chunk(chunk)
        # Compare to ideal square waves
        markDiff = self.__compare_samples(self.rx_mark, decChunk)
        spaceDiff = self.__compare_samples(self.rx_space, decChunk)
        if(markDiff < spaceDiff):
            return "1"
        else:
            return "0"

    # Get bits from wav data
    def __get_bits_from_wav_data(self, frames: bytes) -> str:
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
            start_sample = self.__recover_clock_index(exp_frames) 
            
            # If no start sample could be found we can't decode
            if(start_sample == -1): 
                return ""
            
            # Decode to bits (including training block, we'll trim it off later)
            chunk_iter = int(self.unit_time) + start_sample 
            while(chunk_iter < nFrames - 1):
                chunk = exp_frames[int(chunk_iter - self.unit_time):int(chunk_iter)]
                # End decode when no more data is being transmitted
                if(self.__avg_deviation_array(chunk) < self.amp_end_threshold): 
                    break
                bits += self.__get_bit_value(chunk)
                chunk_iter += self.unit_time
            return bits

    # Trim the training block off of received bits
    def __trim_training_block(self, data: str) -> str:
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
    def __get_bytes_from_bits(self, b_data: str) -> bytes:
        int_data = []
        i = 0
        while(i < len(b_data)):
            int_data.append(int(b_data[(i):(i+8)], 2))
            i += 8
        return bytes(int_data)
    
    # Run error correction and remove all parity bits from bits data
    def __get_data_from_ecc(self, data: str) -> str:
        data_bytes = []
        decoded_bytes = []
        data_iter = 0
        self.ecc.reset_error_count()
        while(data_iter < len(data) - 11):
            data_bytes.append(data[data_iter:data_iter+12])
            data_iter += 12
        for dataByte in data_bytes:
            decoded_bytes.append(self.ecc.decode(dataByte))
        output = "".join(decoded_bytes)
        return output, self.ecc.get_error_count()
    
    # One call to receive bytes data from default audio input (timeout in seconds, disabled by default)
    def rx(self, timeout=-1):
        wav_data = self.__auto__record(timeout)
        if(wav_data == b""): # if timed out
            return b"", 0
        bd = self.__get_bits_from_wav_data(wav_data)
        if(bd == ""): # if no good data
            return b"", 0
        bd = self.__trim_training_block(bd)
        decoded_bin, error_count = self.__get_data_from_ecc(bd)
        bytes_data = self.__get_bytes_from_bits(decoded_bin)
        return bytes_data, error_count

################################################################################ TX TOOLS
class DigitalTransmitter:
    def __init__(self, 
    digital_modulation_type = DigitalModulationTypes.default(),
    training_sequence_time = TRAINING_SEQUENCE_TIME):
        self.digital_modulation_type = digital_modulation_type
        self.ts_oscillations = DigitalModulationTypes.get_ts_oscillations(training_sequence_time, self.digital_modulation_type)
        self.unit_time = DigitalModulationTypes.get_unit_time(self.digital_modulation_type)
        ideal_waves = IdealWaves(digital_modulation_type = self.digital_modulation_type)
        self.tx_space = ideal_waves.get_tx_space()
        self.tx_mark = ideal_waves.get_tx_mark()
        self.tx_silence = ideal_waves.get_tx_silence()
        self.ecc = Hamming()

    # Get bits from bytes
    def __get_bits_from_bytes(self, b_in: bytes) -> str:
        bits = ""
        for i in range(len(b_in)):
            bits += '{0:08b}'.format(b_in[i])
        return bits

    # Encode bits to audio
    def __encode(self, bits: str) -> bytes:
        out_frames = []
        # Pad the start of the file with silence
        out_frames += self.tx_silence
        # Write the data freqs to the file
        for bit in bits:
            if(bit == "0"):
                out_frames += self.tx_space
            else:
                out_frames += self.tx_mark
        # Pad the end of the file with silence
        out_frames += self.tx_silence
        return bytes(out_frames)

    # Generate training block
    def __make_training_block(self) -> str:
        output = "10" * self.ts_oscillations
        output += "1"
        output += "0" * 3
        return output

    # Generate and insert ECC into the data.
    def __insert_ecc(self, data: str) -> str:
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

    # Play a sound from wav data
    def __play_wav_data(self, data: bytes):
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

    def tx(self, data: bytes): # One call to send bytes data over default audio output
        message_bits = self.__get_bits_from_bytes(data)
        ecc_bits = self.__insert_ecc(message_bits)
        training_block = self.__make_training_block()
        tx_bits = training_block + ecc_bits
        out_frames = self.__encode(tx_bits)
        self.__play_wav_data(out_frames)
    
    def est_tx_time(self, data_length: int): # Estimate transmission time in seconds
        return (self.ts_oscillations * 2 + data_length * 12) / (SAMPLE_RATE / self.unit_time)
