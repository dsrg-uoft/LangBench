#!/usr/bin/env python3

from typing import List, Tuple
import sys
import socket
import multiprocessing

def build_header(code: int, body: bytes) -> bytes:
	status: bytes = None
	if code == 200:
		status = b"OK"
	elif code == 404:
		status = b"Not Found"
	else:
		assert(False)
	res: bytes = b"HTTP/1.0 " + str(code).encode("ascii") + b" " + status + b"\r\n"
	res += b"Content-Type: text/plain; charset=UTF-8\r\n"
	res += b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
	res += b"\r\n"
	return res

def read_file(path: str, directory: str) -> bytes:
	parts: List[str] = path.split("/")
	filtered: str = ""
	i: int = 1
	while i < len(parts):
		p: str = parts[i]
		if p == "..":
			continue
		filtered += "/" + p
		i += 1
	filtered = directory + filtered
	try:
		with open(filtered, mode="rb") as f:
			return f.read()
	except IOError:
		return None

def readall(conn: socket.socket) -> None:
	while True:
		buf: bytes = conn.recv(256)
		if len(buf) == 0:
			break

def handle_client(conn: socket.socket, directory: str) -> None:
	f = conn.makefile(buffering=1, encoding="ascii", newline="\r\n")
	line: str = f.readline()
	parts: List[str] = line.split()
	path: str = parts[1]
	data: bytes = read_file(path, directory)
	header: bytes = None
	if data is None:
		data = b"Not found."
		header = build_header(404, data)
	else:
		header = build_header(200, data)
	conn.sendall(header)
	conn.sendall(data)
	readall(conn)
	#print("[trace] closing connection.");
	conn.close()

def main(args: List[str]) -> None:
	with socket.socket() as s:
		#s.bind(("127.0.0.1", int(args[0])))
		s.bind((args[0], int(args[1])))
		s.listen(1025)
		while True:
			conn: socket.socket
			addr: Tuple[str, int]
			conn, addr = s.accept()
			p: multiprocessing.Process = multiprocessing.Process(target=handle_client, args=(conn, args[2]), daemon=False)
			p.start()

if __name__ == '__main__':
	main(sys.argv[1:])
