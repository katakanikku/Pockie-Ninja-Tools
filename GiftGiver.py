import socket
import time
import selectors
import PNUtils


def extract_opcode(data):
    op = ""
    for b in data:
        if b == 124:
            break
        op += chr(b)
    return op


def handle_request(opcode, conn, data):
    print(int(opcode))
    switch = {
        10001: pong,
    }
    switch.get(int(opcode), lambda a, b: print(f"Unknown opcode: {opcode}"))(conn, data)


def pong(conn, data):
    msg = bytearray()
    PNUtils.write_string(msg, "19998")
    conn.send(msg)

    giftInput = input("Input account and gift ID '<name> <id>'\n")
    args = giftInput.split(" ")
    if len(args) != 2:
        print("Invalid args length")
        exit()
    try:
        args[1] = int(args[1])
    except:
        print("Gift id not int")
        exit()
    now = int(round(time.time() * 1000))
    buffer = bytearray()
    PNUtils.write_string(buffer, f"1|{args[0]}!0-1|0|{args[1]}")
    conn.send(buffer)


def read(conn, mask):
    data = conn.recv(1024)
    if data:
        handle_request(extract_opcode(data[4:]), conn, data)
    else:
        print(f"Closing connection with {conn}")
        sel.unregister(conn)
        conn.close()


def accept(sock, mask):
    conn, address = sock.accept()
    print(f"Connection established with {address}")
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)
    # ACK
    conn.send("".encode())

sel = selectors.DefaultSelector()
giftSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
giftSocket.bind(('127.0.0.1', 9988))
giftSocket.listen()

print("Listening...")
giftSocket.setblocking(False)
sel.register(giftSocket, selectors.EVENT_READ, accept)
while True:
    for key, mask in sel.select():
        callback = key.data
        callback(key.fileobj, mask)


# print()

