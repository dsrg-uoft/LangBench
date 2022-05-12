

import java.io.File;
import java.io.FileInputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class SudokuPartialVerifyTimed {
	public static long partial_verify_time = 0;
	static public class SudokuBoard {
		public int[][] board;

		public SudokuBoard() {
			this.board = new int[9][9];
		}

		public void print_board() {
			for (int i = 0; i < 9; i++) {
				for (int j = 0; j < 9; j++) {
					System.out.print(this.board[i][j]);
				}
				System.out.print("\n");
			}
		}

		private boolean partial_verify(int x, int y) {
			int base_x = (x / 3) * 3;
			int base_y = (y / 3) * 3;
			for (int i = 0; i < 9; i++) {
				if (i != y && this.board[x][i] == this.board[x][y]) {
					return false;
				}
				if (i != x && this.board[i][y] == this.board[x][y]) {
					return false;
				}
				int pos_x = base_x + (i / 3);
				int pos_y = base_y + (i % 3);
				if ((pos_x != x || pos_y != y) && this.board[pos_x][pos_y] == this.board[x][y]) {
					return false;
				}
			}
			return true;
		}

		public boolean solve(int x, int y) {
			int z = x * 9 + y + 1;
			if (z == 82) {
				return true;
			}
			if (this.board[x][y] != 0) {
				return this.solve(z / 9, z % 9);
			}
			for (int i = 1; i <= 9; i++) {
				this.board[x][y] = i;
				long t0 = System.nanoTime();
				boolean ok = this.partial_verify(x, y);
				long t1 = System.nanoTime();
				SudokuPartialVerifyTimed.partial_verify_time += t1 - t0;
				if (ok) {
					if (this.solve(z / 9, z % 9)) {
						return true;
					}
				}
			}
			this.board[x][y] = 0;
			return false;
		}

		public boolean verify() {
			for (int i = 0; i < 9; i++) {
				boolean[] row_check = new boolean[10];
				boolean[] col_check = new boolean[10];
				for (int j = 0; j < 9; j++) {
					if (this.board[i][j] == 0) {
						return false;
					}
					if (row_check[this.board[i][j]]) {
						return false;
					}
					row_check[this.board[i][j]] = true;

					if (col_check[this.board[j][i]]) {
						return false;
					}
					col_check[this.board[j][i]] = true;
				}
			}

			for (int i = 0; i < 9; i += 3) {
				for (int j = 0; j < 9; j += 3) {
					boolean[] check = new boolean[10];
					for (int k = 0; k < 9; k++) {
						int x = i + (k / 3);
						int y = j + (k % 3);
						if (check[this.board[x][y]]) {
							return false;
						}
						check[this.board[x][y]] = true;
					}
				}
			}
			return true;
		}

		public boolean read_line(String line) {
			for (int i = 0; i < 9; i++) {
				for (int j = 0; j < 9; j++) {
					char ch = line.charAt(i * 9 + j);
					if (ch == '.') {
						ch = '0';
					}
					this.board[i][j] = ch - '0';
				}
			}
			return true;
		}
	}

	public static void process(String fname) {
		try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(fname), StandardCharsets.UTF_8))) {
			while (true) {
				SudokuBoard sb = new SudokuBoard();
				String line = br.readLine();
				if (line == null) {
					break;
				}
				sb.read_line(line);
				//System.out.print("===\n");
				//sb.print_board();
				//System.out.println();
				sb.solve(0, 0);
				//sb.print_board();
				//System.out.println();
				if (!sb.verify()) {
					throw new RuntimeException("badness");
				}
			}
		} catch (IOException ex) {
			throw new RuntimeException(ex);
		}
	}

	public static void main(String[] args) {
		process(args[0]);
		System.out.print("partial verify 0: " + SudokuPartialVerifyTimed.partial_verify_time + "\n");
		SudokuPartialVerifyTimed.partial_verify_time = 0;
		process(args[0]);
		System.out.print("partial verify 1: " + SudokuPartialVerifyTimed.partial_verify_time + "\n");
	}
}
