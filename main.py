import re

class Error:
    def __init__(self, type:str, message:str) -> None:
        self.type = type
        self.message = message

    def __str__(self):
        return f'{self.type} error: {self.message}'
    
def handle_error(error:Error) -> None:
    ''' Handling eventual errors '''
    print(error)
    exit(1)

def check_output(output):
    ''' Check if the output is an error and handle it '''
    if isinstance(output, Error):
        handle_error(output)
    else:
        return output

def validate_link(link:str) -> bool:
    ''' Validate the input link by checking if the string has the correct format and if all characters are alphanumeric '''

    pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    match = re.match(pattern, link)
    return True if match is not None else Error('Validation', 'Input is not a valid link')

def encode_input(input:str) -> bytes:
    ''' Encoding the input into latin-1 '''
    try:
        enc_input = input.encode('latin-1')
        return enc_input
    except UnicodeEncodeError:
        return Error('Encoding', 'Input contains non-latin characters')


def main():
    # input = 'https://www.example.com/こんにちは' # Non-latin characters
    # input = 'https://www.google.com/search?q=python+regex+match+url' # Valid input
    input = 'http://localhost:8888/install.folder'

    # Check if the link is valid
    check_output(validate_link(input))

    print('Link is valid')
    
    # Try encoding the input
    enc_input = check_output(encode_input(input))
    print(enc_input)
    


main()