
const assert = require("assert");
const fs = require("fs");
const readline = require("readline");

function print_board(board) {
	for (let i = 0; i < 9; i++) {
		let row = "";
		for (let j = 0; j < 9; j++) {
			row += board[i][j];
		}
		console.log(row);
	}
}

function partial_verify(board, x, y) {
	let base_x = Math.floor(x / 3) * 3;
	let base_y = Math.floor(y / 3) * 3;
	for (let i = 0; i < 9; i++) {
		if (i != y && board[x][i] == board[x][y]) {
			return false;
		}
		if (i != x && board[i][y] == board[x][y]) {
			return false;
		}
		let pos_x = base_x + Math.floor(i / 3);
		let pos_y = base_y + (i % 3);
		if ((pos_x != x || pos_y != y) && board[pos_x][pos_y] == board[x][y]) {
			return false;
		}
	}
	return true;
}

function solve(board, x, y) {
	let z = x * 9 + y + 1;
	if (z == 82) {
		return true;
	}
	if (board[x][y] != 0) {
		return solve(board, Math.floor(z / 9), z % 9);
	}
	for (let i = 1; i <= 9; i++) {
		board[x][y] = i;
		if (partial_verify(board, x, y)) {
			if (solve(board, Math.floor(z / 9), z % 9)) {
				return true;
			}
		}
	}
	board[x][y] = 0;
	return false;
}

function verify(board) {
	for (let i = 0; i < 9; i++) {
		let row_check = new Int8Array(10);
		let col_check = new Int8Array(10);
		for (let j = 0; j < 9; j++) {
			if (board[i][j] == 0) {
				return false;
			}
			if (row_check[board[i][j]] != 0) {
				return false;
			}
			row_check[board[i][j]] = 1;

			if (col_check[board[j][i]] != 0) {
				return false;
			}
			col_check[board[j][i]] = 1;
		}
	}

	for (let i = 0; i < 9; i += 3) {
		for (let j = 0; j < 9; j += 3) {
			let check = new Int8Array(10);
			for (let k = 0; k < 9; k++) {
				let x = i + Math.floor(k / 3);
				let y = j + (k % 3);
				if (check[board[x][y]] != 0) {
					return false;
				}
				check[board[x][y]] = 1;
			}
		}
	}
	return true;
}

function read_line(line, board) {
	z = '0'.charCodeAt(0);
	for (let i = 0; i < 9; i++) {
		for (let j = 0; j < 9; j++) {
			let ch = line[i * 9 + j];
			if (ch == '.') {
				ch = '0';
			}
			board[i][j] = ch.charCodeAt(0) - z;
		}
	}
}

function read_file(fname, callback) {
	let rl = readline.createInterface({
		input: fs.createReadStream(fname, { encoding: 'utf-8' }),
		crlfDelay: Infinity,
	});
	rl.on("line", function(line) {
		assert(line.length == 81);
		//let board = new Array(9);
		let board = [];
		for (let i = 0; i < 9; i++) {
			//board[i] = new Int8Array(9);
			board.push(new Int8Array(9));
		}
		read_line(line, board);
		callback(board);
	});
}

function main(args) {
	read_file(args[0], function(board) {
		//console.log("===");
		//print_board(board);
		//console.log();
		solve(board, 0, 0);
		//print_board(board);
		//console.log();
		assert(verify(board));
	});
}

if (!module.parent) {
	main(process.argv.slice(2));
}
