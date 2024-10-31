import sys
import numpy as np
from PIL import Image

def encode_data(data):
    mode_indicator = '0100'
    char_count = '{:08b}'.format(len(data))
    data_bits = ''.join(['{:08b}'.format(ord(c)) for c in data])
    bits = mode_indicator + char_count + data_bits
    return bits

def pad_data_bits(bits, total_data_bits):
    max_terminator_bits = min(4, total_data_bits - len(bits))
    bits += '0' * max_terminator_bits
    while len(bits) % 8 != 0:
        bits += '0'
    pad_bytes = ['11101100', '00010001']
    i = 0
    while len(bits) < total_data_bits:
        bits += pad_bytes[i % 2]
        i += 1
    return bits

def init_galois_tables():
    exp_table = [0] * 512
    log_table = [0] * 256
    x = 1
    for i in range(255):
        exp_table[i] = x
        log_table[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11d
    for i in range(255, 512):
        exp_table[i] = exp_table[i - 255]
    return exp_table, log_table

def gf_mul(a, b, exp_table, log_table):
    if a == 0 or b == 0:
        return 0
    return exp_table[(log_table[a] + log_table[b]) % 255]

def gf_poly_mul(p, q, exp_table, log_table):
    result = [0] * (len(p) + len(q) - 1)
    for i in range(len(p)):
        for j in range(len(q)):
            result[i + j] ^= gf_mul(p[i], q[j], exp_table, log_table)
    return result

def reed_solomon_generator_poly(nsym, exp_table, log_table):
    g = [1]
    for i in range(nsym):
        g = gf_poly_mul(g, [1, exp_table[i]], exp_table, log_table)
    return g

def gf_poly_divmod(dividend, divisor, exp_table, log_table):
    result = list(dividend)
    for i in range(len(dividend) - len(divisor) + 1):
        coef = result[i]
        if coef != 0:
            for j in range(1, len(divisor)):
                if divisor[j] != 0:
                    result[i + j] ^= gf_mul(divisor[j], coef, exp_table, log_table)
    remainder = result[-(len(divisor) - 1):]
    return remainder

def reed_solomon_encode_msg(data_codewords, nsym, exp_table, log_table):
    gen = reed_solomon_generator_poly(nsym, exp_table, log_table)
    msg = data_codewords + [0] * nsym
    remainder = gf_poly_divmod(msg, gen, exp_table, log_table)
    return remainder

def place_finder_patterns(matrix, reserved):
    size = len(matrix)
    positions = [(0, 0), (size - 7, 0), (0, size - 7)]
    for (row, col) in positions:
        for r in range(7):
            for c in range(7):
                if (r == 0 or r == 6 or c == 0 or c == 6) or (2 <= r <= 4 and 2 <= c <= 4):
                    matrix[row + r][col + c] = 1
                else:
                    matrix[row + r][col + c] = 0
                reserved[row + r][col + c] = True
        for r in range(-1, 8):
            if 0 <= row + r < size:
                if col - 1 >= 0:
                    matrix[row + r][col - 1] = 0
                    reserved[row + r][col - 1] = True
                if col + 7 < size:
                    matrix[row + r][col + 7] = 0
                    reserved[row + r][col + 7] = True
        for c in range(-1, 8):
            if 0 <= col + c < size:
                if row - 1 >= 0:
                    matrix[row - 1][col + c] = 0
                    reserved[row - 1][col + c] = True
                if row + 7 < size:
                    matrix[row + 7][col + c] = 0
                    reserved[row + 7][col + c] = True

def place_timing_patterns(matrix, reserved):
    size = len(matrix)
    for i in range(8, size - 8):
        value = (i + 1) % 2
        matrix[6][i] = value
        matrix[i][6] = value
        reserved[6][i] = True
        reserved[i][6] = True

def place_format_information_areas(reserved):
    size = len(reserved)
    for i in range(9):
        if i != 6:
            reserved[i][8] = True
    for i in range(size - 8, size):
        reserved[i][8] = True
    for i in range(9):
        if i != 6:
            reserved[8][i] = True
    for i in range(size - 8, size):
        reserved[8][i] = True

def initialize_matrix(version):
    size = 21
    matrix = np.zeros((size, size), dtype=int)
    reserved = np.zeros((size, size), dtype=bool)
    place_finder_patterns(matrix, reserved)
    place_timing_patterns(matrix, reserved)
    place_format_information_areas(reserved)
    return matrix, reserved

def place_data_bits(matrix, reserved, data_bits):
    size = len(matrix)
    direction = -1
    row = size - 1
    col = size - 1
    bit_index = 0
    while col > 0:
        if col == 6:
            col -= 1
        r = row
        while 0 <= r < size:
            for c in [col, col - 1]:
                if not reserved[r][c]:
                    if bit_index < len(data_bits):
                        matrix[r][c] = int(data_bits[bit_index])
                        bit_index += 1
                    else:
                        matrix[r][c] = 0
                    reserved[r][c] = True
            r += direction
        direction *= -1
        col -= 2

def apply_mask(matrix, reserved):
    size = len(matrix)
    for r in range(size):
        for c in range(size):
            if not reserved[r][c]:
                if (r + c) % 2 == 0:
                    matrix[r][c] ^= 1

def place_format_information(matrix):
    size = len(matrix)
    format_bits = '111011111000100'
    for i in range(6):
        bit = int(format_bits[i])
        matrix[8][i] = bit
    matrix[8][7] = int(format_bits[6])
    matrix[8][8] = int(format_bits[7])
    for i in range(8, 15):
        bit = int(format_bits[i])
        matrix[14 - i][8] = bit
    for i in range(7):
        bit = int(format_bits[i])
        matrix[size - 1 - i][8] = bit
    for i in range(7):
        bit = int(format_bits[7 + i])
        matrix[8][size - 7 + i] = bit

def render_matrix(matrix, scale=10):
    size = len(matrix)
    img_size = size * scale
    img = Image.new('1', (img_size, img_size), 1)
    pixels = img.load()
    for r in range(size):
        for c in range(size):
            color = matrix[r][c]
            for i in range(scale):
                for j in range(scale):
                    pixels[c * scale + j, r * scale + i] = 0 if color else 1
    return img

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate-qr.py <link> <output path>")
        sys.exit(1)

    link = sys.argv[1]
    output_path = sys.argv[2]

    data_bits = encode_data(link)
    total_data_bits = 152
    if len(data_bits) > total_data_bits:
        print("Data too long for version 1-L QR code")
        sys.exit(1)
    data_bits = pad_data_bits(data_bits, total_data_bits)

    data_codewords = []
    for i in range(0, len(data_bits), 8):
        byte = int(data_bits[i:i+8], 2)
        data_codewords.append(byte)

    exp_table, log_table = init_galois_tables()
    nsym = 7
    ecc_codewords = reed_solomon_encode_msg(data_codewords, nsym, exp_table, log_table)
    codewords = data_codewords + ecc_codewords
    codeword_bits = ''.join(['{:08b}'.format(cw) for cw in codewords])

    matrix, reserved = initialize_matrix(1)
    place_data_bits(matrix, reserved, codeword_bits)
    apply_mask(matrix, reserved)
    place_format_information(matrix)

    img = render_matrix(matrix)
    img.save(output_path)

if __name__ == '__main__':
    main()
