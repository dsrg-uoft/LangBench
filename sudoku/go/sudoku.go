package main

import "os"
import "fmt"
import "bufio"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

func print_board(board *[9][9]int) {
	var str []byte = make([]byte, 0, 90)
	var ascii_zero byte = "0"[0]
	var ascii_nl byte = "\n"[0]
	for i := 0; i < 9; i++ {
		for j := 0; j < 9; j++ {
			str = append(str, byte(board[i][j]) + ascii_zero)
		}
		str = append(str, ascii_nl)
	}
	fmt.Printf("%s", string(str))
}

func partial_verify(board *[9][9]int, x int, y int) bool {
	var base_x int = (x / 3) * 3
	var base_y int = (y / 3) * 3
	for i := 0; i < 9; i++ {
		if (i != y) && (board[x][i] == board[x][y]) {
			return false
		}
		if (i != x) && (board[i][y] == board[x][y]) {
			return false
		}
		var pos_x int = base_x + (i / 3)
		var pos_y int = base_y + (i % 3)
		if (pos_x != x || pos_y != y) && (board[pos_x][pos_y] == board[x][y]) {
			return false
		}
	}
	return true
}

func solve(board *[9][9]int, x int, y int) bool {
	var z int = (x * 9) + y + 1
	if z == 82 {
		return true
	}
	if board[x][y] != 0 {
		return solve(board, z / 9, z % 9)
	}
	for i := 1; i <= 9; i++ {
		board[x][y] = i
		if partial_verify(board, x, y) {
			if solve(board, z / 9, z % 9) {
				return true
			}
		}
	}
	board[x][y] = 0
	return false
}

func verify(board *[9][9]int) bool {
	for i := 0; i < 9; i++ {
		var row_check [10]bool
		var col_check [10]bool
		for j := 0; j < 9; j++ {
			if board[i][j] == 0 {
				return false
			}
			if row_check[board[i][j]] {
				return false
			}
			row_check[board[i][j]] = true
			if col_check[board[i][j]] {
				return false
			}
			col_check[board[i][j]] = true
		}
	}
	for i := 0; i < 9; i += 3 {
		for j := 0; j < 9; j += 3 {
			var check [10]bool
			for k := 0; k < 9; k++ {
				var x int = i + (k / 3)
				var y int = j + (k % 3)
				if check[board[x][y]] {
					return false
				}
				check[board[x][y]] = true
			}
		}
	}
	return true
}

func read_line(line string, board *[9][9]int) {
	var ascii_zero byte = "0"[0]
	var ascii_dot byte = "."[0]
	for i := 0; i < 9; i++ {
		for j := 0; j < 9; j++ {
			var ch byte = line[(i * 9) + j]
			if ch == ascii_dot {
				ch = ascii_zero
			}
			board[i][j] = int(ch - ascii_zero)
		}
	}
}

func process(path string) {
	file, err := os.Open(path)
	assert(err == nil)
	defer file.Close()
	var scanner *bufio.Scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		var board [9][9]int
		read_line(scanner.Text(), &board)
		//print_board(&board)
		solve(&board, 0, 0)
		//print_board(&board)
		assert(verify(&board))
	}
}

func main() {
	process(os.Args[1])
}
