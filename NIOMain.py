import asyncio
import PNUtils
import random
import threading
import scrypt
from GameServerHandler import GameServer


class StallServer(asyncio.Protocol):

    def __init__(self, current_connections):
        self.current_connections = current_connections
        self.transport = None
        self.ip = None
        self.index = None
        self.serial = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.ip = self.transport.get_extra_info("peername")[0]
        self.transport.write(bytearray())
        self.transport.write(bytes.fromhex('04 00 00 00 ef ee ee ee'))

    def connection_lost(self, exc):
        print("connection_lost")
        try:
            self.disconnect_user()
            del current_connections[(self.index, self.serial)]
            self.prune_channels()
        except:
            print("err")

    def data_received(self, data: bytes):
        data_copy = bytearray(data)
        for packet in PNUtils.split_packets(data_copy):
            PNUtils.decode(packet)
            if packet:
                self.handle_client_request(packet[4], packet)
            else:
                print("NO PACKET FROM CLIENT")
                self.transport.close()

    def handle_client_request(self, opcode, buffer):
        print("Client")
        print(opcode)
        switch = {
            2: self.login,
            51: self.handle_create_role,
            52: self.get_in_game,
            54: self.heartbeat,
            53: self.select_object,
            56: self.select_object,
            55: self.select_object
        }
        switch.get(opcode, self.unknown_packet)(buffer)

    def handle_create_role(self, buffer):
        msg = bytearray()
        role_json = buffer[12: 12 + buffer[8]]
        print(role_json.decode())
        PNUtils.write_int(msg, 4 + 4 + 4 + 4 + 4 + len(role_json))
        # Message type 9
        PNUtils.write_int(msg, 9)
        # Index
        PNUtils.write_int(msg, self.index)
        # Serial
        PNUtils.write_int(msg, self.serial)
        # Message type 51 for create role
        PNUtils.write_int(msg, 51)
        # JSON Role Info
        try:
            PNUtils.write_string(msg, role_json.decode())
        except:
            print("could not create role")
            print(role_json.decode())
            return
        game_server.send(msg)

    #         Send signal to disconnect user to game server
    def disconnect_user(self):
        # # Length of packet
        msg = bytearray()
        PNUtils.write_int(msg, 4 + 4 + 4)
        PNUtils.write_int(msg, 8)
        # Index
        PNUtils.write_int(msg, self.index)
        # Serial
        PNUtils.write_int(msg, self.serial)
        game_server.send(msg)

    def prune_channels(self):
        for i in channels:
            for j in channels[i]:
                if j not in self.current_connections.copy():
                    channels[i].remove(j)

    def heartbeat(self, buffer):
        print("".join(chr(x) for x in buffer))
        msg = bytearray(PNUtils.int_to_little_endian(4 + 4 + 4 + len(buffer[4:])))
        # Message type 9
        PNUtils.write_int(msg, 9)
        # Index
        PNUtils.write_int(msg, self.index)
        # Serial
        PNUtils.write_int(msg, self.serial)
        msg.extend(buffer[4:])
        print(list(msg))
        print("".join(chr(x) for x in msg))
        game_server.send(msg)

    def unknown_packet(self, buffer):
        print("Unknown")
        print("".join(chr(x) for x in buffer))
        for b in buffer:
            print(b)
        print(list(buffer))

    def get_in_game(self, buffer):
        msg = bytearray()
        PNUtils.write_int(msg, 4 + 4 + 4 + len(buffer[4:]))
        # Message type 9
        PNUtils.write_int(msg, 9)
        # Index
        PNUtils.write_int(msg, self.index)
        # Serial
        PNUtils.write_int(msg, self.serial)
        # Rest of the message
        msg.extend(buffer[4:])
        game_server.send(msg)

    # login to the server
    def login(self, buffer):
        # Get login info from buffer
        username = PNUtils.read_string(buffer, 12, buffer[8])
        password = PNUtils.read_string(buffer, 12 + buffer[8] + 4, buffer[12 + buffer[8]])
        login_details = bytearray()
        index = random.randint(0, 2147483647)
        serial = random.randint(0, 2147483647)
        self.index = index
        self.serial = serial
        # Length of packet
        PNUtils.write_int(login_details, 4 + 4 + len(username) + 4 + 129 + 4 + len(self.ip) + 1 + 4 + 4)
        # Write type. 6 = login packet
        PNUtils.write_int(login_details, 6)
        # Username
        PNUtils.write_string(login_details, username)
        print(len(password))
        # Password
        PNUtils.write_string(login_details, ''.join('{:02x}'.format(x) for x in scrypt.hash(password[:len(password)-1], "LAVASTALLHASHSECRET")) + password[len(password)-1])
        print(login_details)
        print(list(login_details))
        # IP
        PNUtils.write_int(login_details, len(self.ip) + 1)
        login_details.extend(map(ord, self.ip))
        login_details.append(0)
        # Index
        PNUtils.write_int(login_details, self.index)
        # Serial
        PNUtils.write_int(login_details, self.serial)
        game_server.send(login_details)
        # Add connection to current connection list
        current_connections[(self.index, self.serial)] = self.transport
        print(f"TALK ID ADDED: {(self.index, self.serial)}")
        print(self.current_connections)
        # print(self.current_connections_aliases)
        print("Conn added")

    def select_object(self, buffer):
        msg = bytearray(PNUtils.int_to_little_endian(4 + 4 + 4 + len(buffer[4:])))
        # Message type 9
        PNUtils.write_int(msg, 9)
        PNUtils.write_int(msg, self.index)
        # Serial
        PNUtils.write_int(msg, self.serial)
        msg.extend(buffer[4:])
        game_server.send(msg)


async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: StallServer(current_connections),
        '10.0.0.4', 7001)
    print("Server started")
    async with server:
        await server.serve_forever()


current_connections = {}
channels = {}

game_server = GameServer(current_connections, channels)
threading.Thread(target=game_server.start).start()
asyncio.run(main())
