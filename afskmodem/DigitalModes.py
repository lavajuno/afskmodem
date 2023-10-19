"""
    DigitalModes defines the speeds at which AFSKmodem can operate, 
    and the tones that they use.
"""
class DigitalModes:
    def __init__(self):
        self.SAMPLE_RATE = 48000
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