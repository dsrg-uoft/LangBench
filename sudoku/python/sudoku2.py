#!/usr/bin/env python3

import sys
#import cProfile
import dis

def print_board(board):
	for i in range(9):
		line = ""
		for j in range(9):
			line += str(board[i][j])
		print(line)

def partial_verify(board, x, y):
	base_x = (x // 3) * 3
	base_y = (y // 3) * 3
	for i in range(9):
		cond_1 = (i != y)
		xi = board[x][i]
		xy = board[x][y]
		cond_2 = (xi == xy)
		if cond_1 and cond_2:
		#if (i != y) and (board[x][i] == board[x][y]):
			return False
		if (i != x) and (board[i][y] == board[x][y]):
			return False
		pos_x = base_x + (i // 3)
		pos_y = base_y + (i % 3)
		if ((pos_x != x) or (pos_y != y)) and (board[pos_x][pos_y] == board[x][y]):
			return False
	return True

def solve(board, x, y):
	z = x * 9 + y + 1
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

def verify(board):
	for i in range(9):
		row_check = [ False ] * 10
		col_check = [ False ] * 10
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
			check = [ False ] * 10;
			for k in range(9):
				x = i + (k // 3)
				y = j + (k % 3)
				if check[board[x][y]]:
					return False
				check[board[x][y]] = True
	return True

def read_line(buf, board):
	z = ord('0')
	for i in range(9):
		for j in range(9):
			ch = buf[i * 9 + j]
			if ch == ".":
				ch = "0"
			board[i][j] = ord(ch) - z

def process(fname):
	with open(fname) as f:
		for line in f:
			board = []
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
	return 0

def target(*args):
	return main, None

if __name__ == '__main__':
	main(sys.argv[1:])
