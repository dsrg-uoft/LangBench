#include <iostream>
#include <fstream>
#include <memory>
#include <cassert>

class SudokuBoard {
public:
	int* operator[](int i) {
		return this->board[i];
	}
	virtual bool partial_verify(int x, int y) = 0;
	virtual bool solve(int x, int y) = 0;
	virtual bool verify() = 0;
	virtual bool read_line(std::istream* is) = 0;
	virtual ~SudokuBoard() = 0;
private:
	int board[9][9];
};
SudokuBoard::~SudokuBoard() = default;

class SudokuBoardImpl : public SudokuBoard {
	virtual bool partial_verify(int x, int y) override {
		int base_x = (x / 3) * 3;
		int base_y = (y / 3) * 3;
		for (int i = 0; i < 9; i++) {
			if (i != y && (*this)[x][i] == (*this)[x][y]) {
				return false;
			}
			if (i != x && (*this)[i][y] == (*this)[x][y]) {
				return false;
			}
			int pos_x = base_x + (i / 3);
			int pos_y = base_y + (i % 3);
			if ((pos_x != x || pos_y != y) && (*this)[pos_x][pos_y] == (*this)[x][y]) {
				return false;
			}
		}
		return true;
	}

	virtual bool solve(int x, int y) override {
		int z = x * 9 + y + 1;
		if (z == 82) {
			return true;
		}
		if ((*this)[x][y] != 0) {
			return this->solve(z / 9, z % 9);
		}
		for (int i = 1; i <= 9; i++) {
			(*this)[x][y] = i;
			if (this->partial_verify(x, y)) {
				if (this->solve(z / 9, z % 9)) {
					return true;
				}
			}
		}
		(*this)[x][y] = 0;
		return false;
	}

	virtual bool verify() override {
		for (int i = 0; i < 9; i++) {
			bool row_check[10] = {};
			bool col_check[10] = {};
			for (int j = 0; j < 9; j++) {
				if ((*this)[i][j] == 0) {
					return false;
				}
				if (row_check[(*this)[i][j]]) {
					return false;
				}
				row_check[(*this)[i][j]] = 1;

				if (col_check[(*this)[j][i]]) {
					return false;
				}
				col_check[(*this)[j][i]] = 1;
			}
		}

		for (int i = 0; i < 9; i += 3) {
			for (int j = 0; j < 9; j += 3) {
				bool check[10] = {};
				for (int k = 0; k < 9; k++) {
					int x = i + (k / 3);
					int y = j + (k % 3);
					if (check[(*this)[x][y]]) {
						return false;
					}
					check[(*this)[x][y]] = 1;
				}
			}
		}
		return true;
	}

	bool read_line(std::istream* is) {
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
				(*this)[i][j] = ch - '0';
			}
		}
		return true;
	}

};

void process(char* fname) {
	std::ifstream f(fname);
	while (true) {
		std::unique_ptr<SudokuBoard> board = std::make_unique<SudokuBoardImpl>();
		if (!board->read_line(&f)) {
			break;
		}
		board->solve(0, 0);
		assert(board->verify());
	}
}

int main(int argc, char* argv[]) {
	process(argv[1]);
}
