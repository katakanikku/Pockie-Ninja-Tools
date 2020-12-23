import asyncio
import socket
import selectors
import select
import PNUtils
import keyboard
from collections import deque


class GameServer:
    current_connections: dict
    channels: dict
    message_list: deque

    def __init__(self, current_connections, channels):
        self.current_connections = current_connections
        self.channels = channels
        self.game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.game_socket.connect(("localhost", 7999))
        self.message_list = deque()
        # self.game_socket.settimeout(1)
        self.game_socket.setblocking(False)

    def send(self, data):
        self.game_socket.send(data)
        # self.message_list.append(data)

    def start(self):
        hello = bytearray()
        PNUtils.write_int(hello, 4)
        PNUtils.write_int(hello, 1)
        self.game_socket.send(hello)
        sel = selectors.DefaultSelector()
        sel.register(self.game_socket, selectors.EVENT_READ, self.server_read)
        while True:
            if keyboard.is_pressed('b'):
                print('server loop')
            for key, mask in sel.select(2):
                callback = key.data
                callback(key.fileobj, mask)
        #     readable, writable, exceptional = select.select([self.game_socket], [self.game_socket], [self.game_socket], 3)
        #     for s in readable:
        #         self.server_read(s, 0)
        #     for s in writable:
        #         if len(self.message_list) > 0:
        #             message = self.message_list.popleft()
        #             s.send(message)
        #     for s in exceptional:
        #         print("EXCEPTION")
        #         exit(1)


    def server_read(self, conn, mask):
        try:
            data = bytearray(conn.recv(1024))
        except:
            print("COULD NOT RETURN BYTES FROM SERVER BUFFER")
            return
        # Read msg len and split up accordingly
        buff = data
        while len(buff) == 1024:
            try:
                buff = bytearray(conn.recv(1024))
            except:
                print("COULD NOT RETURN BYTES FROM SERVER BUFFER")
                return
            data.extend(buff)
        for packet in PNUtils.split_packets(data):
            if packet:
                self.handle_server_request(packet[4], packet, conn)
            else:
                print("NO PACKET FROM SERVER")

    def handle_server_request(self, opcode, buffer: bytearray, conn):
        print("Server")
        print(opcode)
        switch = {
            51: self.return_created_role,
            70: self.send_server_time,
            53: self.send_object,
            56: self.send_object,
            55: self.send_object,
            60: self.send_object,
            59: self.send_object,
            75: self.send_object,
            48: self.handle_channel,
            47: self.send_to_channel,
            46: self.send_to_all,
            65: self.send_object,
            66: self.send_object,
            58: self.send_object,
            67: self.send_object,
            57: self.send_object,
            62: self.send_object,
            71: self.send_object,
            54: self.send_object,
            72: self.send_object,
            68: self.send_object,
            49: self.close_client,
            69: self.send_object,
            99: self.send_object,
            44: self.send_login_return,
            # 73: self.return_account_in_use,
            73: self.send_object,
            52: self.send_object
        }
        switch.get(opcode, self.unknown_packet)(buffer, conn)

    def send_object(self, buffer, conn):
        msg_type = buffer[4:8]
        # if msg_type == PNUtils.int_to_little_endian(68):
        print("".join(chr(x) for x in buffer))
        print(list(buffer))
        # Index
        index = PNUtils.little_endian_bytes_to_int(buffer[8:12])
        # Serial
        serial = PNUtils.little_endian_bytes_to_int(buffer[12:16])
        # JSON object
        msg = bytearray(msg_type)
        msg.extend(buffer[16:])
        # if msg_type == PNUtils.int_to_little_endian(68):
        print("".join(chr(x) for x in msg))
        print(list(msg))
        PNUtils.encode(msg)
        # Message header
        msglen = bytearray(PNUtils.int_to_little_endian(len(msg)))
        msglen.extend(msg)
        self.send_to_talk_id((index, serial), msglen)

    def return_created_role(self, buffer, conn):
        print("Role create")
        print("".join(chr(x) for x in buffer))
        role_info = buffer[20:len(buffer) - 1].decode()
        print(list(buffer))
        print(role_info)
        msg = bytearray()
        index = PNUtils.little_endian_bytes_to_int(buffer[8:12])
        serial = PNUtils.little_endian_bytes_to_int(buffer[12:16])
        if buffer[33] == 48:
            self.send_login_code(buffer, -6969)
            self.current_connections[(index, serial)].close()
            return
        print((index, serial))
        PNUtils.write_int(msg, 51)
        PNUtils.write_string(msg, role_info)
        PNUtils.encode(msg)
        msglen = bytearray()
        PNUtils.write_int(msglen, 4 + 4 + len(role_info))
        msglen.extend(msg)
        self.send_to_talk_id((index, serial), msglen)

    def send_login_code(self, buff, err):
        # Index
        index = PNUtils.little_endian_bytes_to_int(buff[8:12])
        # Serial
        serial = PNUtils.little_endian_bytes_to_int(buff[12:16])
        msg = bytearray(PNUtils.int_to_little_endian(2))
        msg.extend(PNUtils.int_to_little_endian(err))
        PNUtils.encode(msg)
        msglen = bytearray(PNUtils.int_to_little_endian(len(msg)))
        msglen.extend(msg)
        print((index, serial))
        self.send_to_talk_id((index, serial), msglen)

    def send_server_time(self, buffer, conn):
        msg = bytearray()
        # Index
        index = PNUtils.little_endian_bytes_to_int(buffer[8:12])
        # Serial
        serial = PNUtils.little_endian_bytes_to_int(buffer[12:16])
        # JSON of TIME AND TIME1
        msg.extend(buffer[16:])
        msglen = bytearray()
        PNUtils.encode(msg)
        PNUtils.write_int(msglen, len(buffer[16:]))
        msglen.extend(msg)
        self.send_to_talk_id((index, serial), msglen)

    def send_login_return(self, buff, conn):
        print("login return")
        print(list(buff))
        print("".join(chr(x) for x in buff))
        # Index
        index = PNUtils.little_endian_bytes_to_int(buff[8:12])
        # Serial
        serial = PNUtils.little_endian_bytes_to_int(buff[12:16])
        msg = bytearray(PNUtils.int_to_little_endian(2))
        msg.extend(buff[len(buff) - 4:])
        PNUtils.encode(msg)
        msglen = bytearray(PNUtils.int_to_little_endian(len(msg)))
        msglen.extend(msg)
        self.send_to_talk_id((index, serial), msglen)

    def handle_channel(self, buff, conn):
        channel_id = PNUtils.little_endian_bytes_to_int(buff[8:12])
        msg_type = PNUtils.little_endian_bytes_to_int(buff[12:16])
        if msg_type == 1:
            print("channel created: " + str(channel_id))
            self.channels[channel_id] = []
        elif msg_type == 3:
            index = PNUtils.little_endian_bytes_to_int(buff[16:20])
            serial = PNUtils.little_endian_bytes_to_int(buff[20:24])
            try:
                self.channels[channel_id].append(self.current_connections[(index, serial)])
            except:
                print(f"COULD NOT ADD TO CHANNEL " + str(channel_id))

    def send_to_channel(self, buff, conn):
        channel_id = PNUtils.little_endian_bytes_to_int(buff[8:12])
        msg = bytearray(PNUtils.int_to_little_endian(len(buff[12:])))
        data = buff[12:]
        PNUtils.encode(data)
        msg.extend(data)
        try:
            for talk_id in self.channels[channel_id].copy():
                talk_id.write(msg)
        except:
            print("Couldn't send to channel " + str(channel_id))

    def send_to_all(self, buffer, conn):
        # Send to all in buffer
        print(list(buffer))
        msg = bytearray(PNUtils.int_to_little_endian(len(buffer[8:])))
        data = buffer[8:]
        PNUtils.encode(data)
        msg.extend(data)
        print(list(msg))
        for k in self.current_connections.copy():
            self.send_to_talk_id(k, msg)

    def close_client(self, buffer, conn):
        index = PNUtils.little_endian_bytes_to_int(buffer[8:12])
        serial = PNUtils.little_endian_bytes_to_int(buffer[12:16])
        print(f"CLOSING CLIENT {(index, serial)}")
        try:
            self.current_connections[(index, serial)].close()
        except:
            print("Already closed")

    def send_to_talk_id(self, id, msg):
        try:
            self.current_connections[id].write(msg)
        except:
            print("guys dead mate")

    def unknown_packet(self, buffer, conn):
        print("Unknown")
        print("".join(chr(x) for x in buffer))
        for b in buffer:
            print(b)
        print(list(buffer))
