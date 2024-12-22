import sys
import validators # To validate all kinds of links

capacities = {
    1: {'L': 17, 'M': 14, 'Q': 11, 'H': 7},
    2: {'L': 32, 'M': 28, 'Q': 22, 'H': 14},
    3: {'L': 53, 'M': 44, 'Q': 34, 'H': 24},
    4: {'L': 78, 'M': 64, 'Q': 48, 'H': 34},
    5: {'L': 106, 'M': 86, 'Q': 62, 'H': 44},
    6: {'L': 134, 'M': 108, 'Q': 76, 'H': 58},
    7: {'L': 154, 'M': 124, 'Q': 88, 'H': 64},
    8: {'L': 192, 'M': 154, 'Q': 110, 'H': 84},
    9: {'L': 230, 'M': 182, 'Q': 132, 'H': 98},
    10: {'L': 271, 'M': 216, 'Q': 154, 'H': 119}
}

class Error:
    def __init__(self, type:str, message:str) -> None:
        self.type = type
        self.message = message

    def __str__(self):
        return f'{self.type} error: {self.message}'
    
def handle_error(error:Error) -> None:
    ''' Handling eventual errors '''
    print(error)
    sys.exit(1)

def check_output(output):
    ''' Check if the output is an error and handle it '''
    if isinstance(output, Error):
        handle_error(output)
    else:
        return output

def validate_link(link:str) -> bool:
    ''' Validate the input link by checking if the string has the correct format and if all characters are alphanumeric '''

    if validators.url(link):
        return True
    else:
        return Error('Validation', 'Input is not a valid link')

def validate_input_length(input: str, version: int, error_correction: str):
    '''Validate that the input length is within the QR code capacity.'''

    max_capacity = capacities.get(version, {}).get(error_correction)
    if max_capacity is None:
        return Error('Validation', 'Unsupported QR code version or error correction level')
    if len(input.encode('utf-8')) > max_capacity:
        return Error('Input Length', 'Input exceeds maximum QR code capacity')
    return True

def encode_input(input:str) -> bytes:
    ''' Encoding the input into latin-1 '''
    try:
        enc_input = input.encode('utf-8')
        mode_indicator = '0100' # Byte indicating the mode of the input
        char_count = len(enc_input) # Number of characters in the input
        char_count_indicator = f'{char_count:08b}' if char_count < 256 else f'{char_count:016b}'
        data_bits = ''.join(f'{byte:08b}' for byte in enc_input)
        bit_stream = mode_indicator + char_count_indicator + data_bits

        return bit_stream

    except UnicodeEncodeError:
        return Error('Encoding', 'Input contains unsupported characters')

def term_and_padding(bit_stream:bytes) -> bytes:
    ''' Terminating the bit stream and adding padding '''

    max_bits = 152  # Maximum bits for Version 1 QR Code with Low error correction
    remaining_bits = max_bits - len(bit_stream)
    terminator = '0' * min(4, remaining_bits)
    bit_stream += terminator

    # Pad to the next byte boundary
    if len(bit_stream) % 8 != 0:
        bit_stream += '0' * (8 - (len(bit_stream) % 8))

    # Add padding bytes if necessary
    padding_bytes = ['11101100', '00010001']
    i = 0
    while len(bit_stream) < max_bits:
        bit_stream += padding_bytes[i]
        i = (i + 1) % 2

    return bit_stream

def main():
    # input = 'https://www.google.com/search?q=python+regex+match+url'
    # input = 'http://localhost:8888/install.folder'
    # input = 'https://www.youtube.com/watch?v=XQnfFXrOHIY&ab_channel=TsunamiNutrition'

    # if len(sys.argv) != 2:
    #     print("Usage: python3 generate-qr.py <link>")
    #     sys.exit(1)

    # input = sys.argv[1]

    # Check if the link is valid
    check_output(validate_link(input))

    version, error_correction = 1, 'L'

    # Check if the input length is within the QR code capacity
    check_output(validate_input_length(input, version, error_correction))


    
    # Try encoding the input
    bit_stream = check_output(encode_input(input))

    finalized_bit_stream = check_output(term_and_padding(bit_stream))

    print(finalized_bit_stream)
    

if __name__ == '__main__':
    main()