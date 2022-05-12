#!/usr/bin/env python3

import socket
import sys
import threading
from hashmap_concurrent import HashMap
from typing import List

class Client:
	def __init__(self, hashmap: HashMap, s: socket.socket) -> None:
		self.hashmap: HashMap = hashmap
		self.sock: socket.socket = s
		self.buf: bytearray = bytearray()
		self.file = s.makefile(buffering=1, encoding="ascii", newline="\r\n")

	'''
	def find_newline(self) -> bytearray:
		i: int = self.buf.find(b"\r\n")
		if i != -1:
			ret: bytearray = self.buf[:i]
			self.buf = self.buf[i + 2:]
			return ret
		return None

	def socket_readline(self) -> bytearray:
		line: bytearray = self.find_newline()
		if line:
			return line
		while True:
			recv: bytes = self.sock.recv(1024)
			if not recv:
				return None
			self.buf.extend(recv)
			line = self.find_newline()
			if line:
				return line
	'''

	def socket_readline(self) -> str:
		line: str = self.file.readline()[:-2]
		if len(line) == 0:
			return None
		return line

	def handle_connection(self) -> None:
		while True:
			cmd_len_buf: str = self.socket_readline()
			if cmd_len_buf == None:
				return
			cmd_len: int = int(cmd_len_buf[1:])

			cmd: List[str] = [None] * cmd_len
			i: int = 0
			while i < cmd_len:
				buf: str = self.socket_readline()
				assert(buf[0] == '$')
				cmd[i] = self.socket_readline()
				assert(len(cmd[i]) == int(buf[1:]))
				i += 1

			ret: bytes = None
			if cmd[0] == "GET":
				value: str = self.hashmap.get(cmd[1])
				if value == None:
					ret = b"$-1\r\n"
				else:
					ret = b"$" + str(len(value)).encode("ascii") + b"\r\n" + value.encode("ascii") + b"\r\n"
			elif cmd[0] == "SET":
				self.hashmap.set(cmd[1], cmd[2])
				ret = b"+OK\r\n"
			else:
				print("[error] unknown client message: " + str(cmd))
				return
			self.sock.send(ret)
			# print("[info] cmd: {} ret: {}".format(" ".join([str(x) for x in cmd]), ret))

def main(args: List[str]) -> None:
	hashmap: HashMap = HashMap(int(args[2]) * 1024, int(args[3]))
	with socket.socket() as s:
		#s.bind(("127.0.0.1", int(args[0])))
		s.bind((args[0], int(args[1])))
		s.listen(8)
		while True:
			conn, addr = s.accept()
			c: Client = Client(hashmap, conn)
			t: threading.Thread = threading.Thread(target=c.handle_connection, daemon=False)
			t.start()

if __name__ == '__main__':
	main(sys.argv[1:])
