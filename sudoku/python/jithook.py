import pypyjit
from pprint import pprint

def foo(x):
	print("=" * 32)
	print(x.jitdriver_name)
	print(x.greenkey)
	print(x.loop_no)
	print(x.bridge_no)
	print(x.type)
	print(x.asmaddr)
	print(x.asmlen)
	print(x.operations)
	print(dir(x.operations[0]))
	print()

pypyjit.set_compile_hook(foo)

from typing import List
import sys
import cProfile
import dis

def print_board(board: List[List[int]]) -> None:
	for i in range(9):
		line = ""
		for j in range(9):
			line += str(board[i][j])
		print(line)

def partial_verify(board: List[List[int]], x: int, y: int) -> bool:
	base_x: int = (x // 3) * 3
	base_y: int = (y // 3) * 3
	for i in range(9):
		cond_1: bool = (i != y)
		xi: int = board[x][i]
		xy: int = board[x][y]
		cond_2: bool = (xi == xy)
		if cond_1 and cond_2:
		#if (i != y) and (board[x][i] == board[x][y]):
			return False
		if (i != x) and (board[i][y] == board[x][y]):
			return False
		pos_x: int = base_x + (i // 3)
		pos_y: int = base_y + (i % 3)
		if ((pos_x != x) or (pos_y != y)) and (board[pos_x][pos_y] == board[x][y]):
			return False
	return True

def solve(board: List[List[int]], x: int, y: int) -> bool:
	z: int = x * 9 + y + 1
	if (z == 82):
		return True
	if (board[x][y] != 0):
		return solve(board, z // 9, z % 9)
	for i in range(1, 9 + 1):
		board[x][y] = i
		if partial_verify(board, x, y):
			if solve(board, z // 9, z % 9):
				return True
	board[x][y] = 0
	return False

def verify(board: List[List[int]]) -> bool:
	for i in range(9):
		row_check: List[bool] = [ False ] * 10
		col_check: List[bool] = [ False ] * 10
		for j in range(9):
			if board[i][j] == 0:
				return False
			if row_check[board[i][j]]:
				return False
			row_check[board[i][j]] = True

			if (col_check[board[j][i]]):
				return False
			col_check[board[j][i]] = True

	for i in range(0, 9, 3):
		for j in range(0, 9, 3):
			check: List[bool] = [ False ] * 10;
			for k in range(9):
				x: int = i + (k // 3)
				y: int = j + (k % 3)
				if check[board[x][y]]:
					return False
				check[board[x][y]] = True
	return True

def read_line(buf: str, board: List[List[int]]) -> None:
	z = ord('0')
	for i in range(9):
		for j in range(9):
			ch: str = buf[i * 9 + j]
			if ch == ".":
				ch = "0"
			board[i][j] = ord(ch) - z

def process(fname) -> None:
	with open(fname, encoding='utf-8') as f:
		line: str
		for line in f:
			board: List[List[int]] = []
			for i in range(9):
				board.append([ 0 ] * 9)
			read_line(line, board)
			#print("===")
			#print_board(board)
			#print()
			solve(board, 0, 0)
			#print_board(board)
			#print()
			assert(verify(board))
			#cProfile.runctx("verify(board)", globals(), locals())

def main(args):
	process(args[0])
	#cProfile.run("process('" + args[0] + "')")
	#dis.dis(partial_verify)

if __name__ == '__main__':
	main(sys.argv[1:])
