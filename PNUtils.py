# Read string from buffer
import struct


def read_string(buff, start, length):
    string = ""
    for i in range(start, start + length):
        string += chr(buff[i])
    return string


# Write LE int to buffer
def write_int(buff, integer):
    buff.extend(int_to_little_endian(integer))


def write_big_end_int(buff, integer):
    buff.extend(int_to_big_endian(integer))


def int_to_little_endian(integer):
    return struct.pack('<i', integer)


def int_to_big_endian(integer):
    return struct.pack(">i", integer)


# Convert bytes in LE order into integers
def little_endian_bytes_to_int(byteArr):
    return byteArr[3] << 24 | byteArr[2] << 16 | byteArr[1] << 8 | byteArr[0]


def split_packets(buff):
    packets = []
    counter = 0
    while True:
        try:
            p_size = little_endian_bytes_to_int(buff[counter:counter + 4])
        except IndexError:
            break
        packet = bytearray()
        for i in range(counter, counter + p_size + 4):
            try:
                packet.append(buff[counter])
            except:
                break
            counter += 1
        packets.append(packet)
    return packets


# Write string to buffer
def write_string(buff, string):
    write_int(buff, len(string))
    buff.extend(map(ord, string))


# Decode function from PN
def decode(byte_arr: bytearray):
    # decode keys
    decode_key1 = (-269488145).to_bytes(4, byteorder='little', signed=True)
    decode_key2 = (-1162167622).to_bytes(4, byteorder='little', signed=True)

    length = len(byte_arr)
    num = length >> 2
    for i in range(num):
        index = i * 4
        byte_arr[index] = byte_arr[index] ^ decode_key1[0]
        byte_arr[index + 1] = byte_arr[index + 1] ^ decode_key1[1]
        byte_arr[index + 2] = byte_arr[index + 2] ^ decode_key1[2]
        byte_arr[index + 3] = byte_arr[index + 3] ^ decode_key1[3]
    tail_length = length & 3
    if tail_length > 0:
        tail_index = num * 4
        for k in range(tail_length):
            byte_arr[k + tail_index] = byte_arr[k + tail_index] ^ decode_key2[k]


def encode(byte_arr: bytearray):
    encode_key1 = (-286331154).to_bytes(4, byteorder='little', signed=True)
    encode_key2 = (-1414812757).to_bytes(4, byteorder='little', signed=True)

    length = len(byte_arr)
    num = length >> 2
    for i in range(num):
        index = i * 4
        byte_arr[index] = byte_arr[index] ^ encode_key1[0]
        byte_arr[index + 1] = byte_arr[index + 1] ^ encode_key1[1]
        byte_arr[index + 2] = byte_arr[index + 2] ^ encode_key1[2]
        byte_arr[index + 3] = byte_arr[index + 3] ^ encode_key1[3]
    tail_length = length & 3
    if tail_length > 0:
        tail_index = num * 4
        for k in range(tail_length):
            byte_arr[k + tail_index] = byte_arr[k + tail_index] ^ encode_key2[k]
