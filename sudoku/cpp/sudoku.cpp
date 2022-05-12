#include <iostream>
#include <fstream>
#include <vector>
#include <cassert>

typedef std::vector<std::vector<int>> SudokuBoard;

extern "C" {

void print_board(SudokuBoard* board) {
	for (int i = 0; i < 9; i++) {
		for (int j = 0; j < 9; j++) {
			std::cout << (*board)[i][j];
		}
		std::cout << std::endl;
	}
}

bool partial_verify(SudokuBoard* board, int x, int y) {
	int base_x = (x / 3) * 3;
	int base_y = (y / 3) * 3;
	for (int i = 0; i < 9; i++) {
		if (i != y && (*board)[x][i] == (*board)[x][y]) {
			return false;
		}
		if (i != x && (*board)[i][y] == (*board)[x][y]) {
			return false;
		}
		int pos_x = base_x + (i / 3);
		int pos_y = base_y + (i % 3);
		if ((pos_x != x || pos_y != y) && (*board)[pos_x][pos_y] == (*board)[x][y]) {
			return false;
		}
	}
	return true;
}

bool solve(SudokuBoard* board, int x, int y) {
	int z = x * 9 + y + 1;
	if (z == 82) {
		return true;
	}
	if ((*board)[x][y] != 0) {
		return solve(board, z / 9, z % 9);
	}
	for (int i = 1; i <= 9; i++) {
		(*board)[x][y] = i;
		if (partial_verify(board, x, y)) {
			if (solve(board, z / 9, z % 9)) {
				return true;
			}
		}
	}
	(*board)[x][y] = 0;
	return false;
}

bool verify(SudokuBoard* board) {
	for (int i = 0; i < 9; i++) {
		bool row_check[10] = {};
		bool col_check[10] = {};
		for (int j = 0; j < 9; j++) {
			if ((*board)[i][j] == 0) {
				return false;
			}
			if (row_check[(*board)[i][j]]) {
				return false;
			}
			row_check[(*board)[i][j]] = 1;

			if (col_check[(*board)[j][i]]) {
				return false;
			}
			col_check[(*board)[j][i]] = 1;
		}
	}

	for (int i = 0; i < 9; i += 3) {
		for (int j = 0; j < 9; j += 3) {
			bool check[10] = {};
			for (int k = 0; k < 9; k++) {
				int x = i + (k / 3);
				int y = j + (k % 3);
				if (check[(*board)[x][y]]) {
					return false;
				}
				check[(*board)[x][y]] = 1;
			}
		}
	}
	return true;
}

bool read_line(std::istream* is, SudokuBoard* board) {
	int len = 81 + 1;
	char buf[len];
	if (!is->read(buf, len)) {
		return false;
	}
	for (int i = 0; i < 9; i++) {
		for (int j = 0; j < 9; j++) {
			char ch = buf[i * 9 + j];
			if (ch == '.') {
				ch = '0';
			}
			(*board)[i][j] = ch - '0';
		}
	}
	return true;
}

void process(char* fname) {
	std::ifstream f(fname);
	while (true) {
		SudokuBoard board(9, std::vector<int>(9));
		if (!read_line(&f, &board)) {
			break;
		}
		//std::cout << "===" << std::endl;
		//print_board(&board);
		//std::cout << std::endl;
		solve(&board, 0, 0);
		//print_board(&board);
		//std::cout << std::endl;
		assert(verify(&board));
	}
}

}

int main(int argc, char* argv[]) {
	process(argv[1]);
}
