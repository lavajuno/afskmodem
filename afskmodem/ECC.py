"""
    ECC provides functionality for encoding, decoding, and correcting
    bit errors.
"""
class ECC:
    """
        Pad the positions of parity bits in a byte with 0s
        :param bits: (str) Bits to pad (8)
        :return: (str) Padded bits (12)
    """
    def __padParityBits(self, bits: str) -> str:
        j = 0
        k = 1
        pad_bits = ""
        for i in range(1, len(bits) + 5):
            if(i == 2**j):
                pad_bits += '0'
                j += 1
            else:
                pad_bits += bits[-1 * k]
                k += 1
        return pad_bits[::-1]
    
    """
        Trim the parity bits off an encoded byte
        :param bits: (str) Encoded byte to trim (String of 12 bits)
        :return: (str) Decoded byte as a String of 8 bits
    """
    def __trimParityBits(self, data: str) -> str:
        data = data[::-1]
        j = 0
        trimmed_bits = ""
        for i in range(len(data)):
            if(i + 1 != 2 ** j):
                trimmed_bits += data[i]
            else:
                j += 1
        return trimmed_bits[::-1]

    """
        Find an error (if it exists) and return the index
        :param bits: (str) Byte to search for an error
        :return: (str) Index of the error (will be the end of the input if not found)
    """
    def __getErrorIndex(self, data: str) -> int:
        n = len(data)
        p = 0
        for i in range(4):
            k = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    k = k ^ int(data[-1 * j])
            p += k*(10**i)
        return n - int(str(p), 2)
 
    """
        Encodes a byte of data (8 bits -> 12 bits)
        :param bits: (str) Byte to encode (as a string of bits)
        :return: (str) Encoded byte (as a string of bits)
    """
    def __encodeByte(self, bits: str) -> str:
        p_bits = self.__padParityBits(bits)
        n = len(p_bits)
        for i in range(4):
            p = 0
            for j in range(1, n + 1):
                if(j & (2**i) == (2**i)):
                    p = p ^ int(p_bits[-1 * j])
            p_bits = p_bits[:n-(2**i)] + str(p) + p_bits[n-(2**i)+1:]
        return p_bits

    """
        Decodes a byte of data (12 bits -> 8 bits)
        :param bits: (str) Byte to decode (as a string of bits)
        :return: (str, bool) Decoded byte, True if an error was corrected
    """
    def __decodeByte(self, bits: str) -> (str, bool):
        err_index = self.__getErrorIndex(bits)
        if(err_index == len(bits)):
            return (bits, False)
        else:
            bits[err_index] = "0" if bits[err_index] == "1" else "1"
        return (bits, True)

    """
        Corrects errors and decodes data
        :param bits: (str) Bits to decode (length must be multiple of 12)
        :return: (str, int) Decoded bits, number of errors corrected
    """
    def decode(self, bits: str) -> (str, int):
        error_count = 0
        dec_bytes = ""
        for i in range(0, len(bits) - 11, 12):
            (dec_byte, err_found) = self.__decodeByte(bits[i : i + 1])
            dec_bytes += dec_byte
            error_count += 1 if err_found else 0
        return (dec_bytes, error_count)
    
    """
        Encodes data by inserting parity bits
        :param bits: (str) Bits to encode (length must be multiple of 8)
        :return: (str) Encoded bits
    """
    def encode(self, bits: str) -> str:
        enc_bits = ""
        for i in range(0, len(bits) - 7, 8):
            enc_bits += self.__encodeByte(bits[i:i+8])
        return enc_bits