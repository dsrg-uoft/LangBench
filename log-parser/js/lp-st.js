const fs = require("fs");
const readline = require("readline");

function assert(cond) {
	if (!cond) {
		throw new Error("badness");
	}
}

function time_diff(start, end) {
	let sec = end[0] - start[0];
	let nano = end[1] - start[1];
	return sec * 1e9 + nano;
}

let TokenType = Object.freeze({
	PLAIN: 0,
	VARIABLE: 1,
	WILDCARD: 2,
	PLAIN_WILDCARD: 3,
	VARIABLE_WILDCARD: 4,
});

class LogParser {
	constructor(files) {
		this.files = files;
		this.file_tables = new Array(files.length);
		this.formats = [];
		this.format_ids = {};
		this.variables = [];
		this.variable_ids = {};
	}

	index(threads, callback) {
		let x = { value: this.files.length };
		let p = new Promise((resolve, reject) => {
			for (let i = 0; i < this.files.length; i++) {
				process_file(i, this, x, resolve);
			}
		});
		p.then((success) => {
			assert(success);
			console.log("[info] done indexing.");
			callback();
		}).catch((reason) => {
			console.log("[error]", reason);
		});
	}

	format_matches_pattern(format, pattern_parts, pattern_types, pos, part, prev_is_wildcard, results, cur) {
		if (part >= pattern_parts.length) {
			results.push(cur);
			return;
		}
		let token = pattern_parts[part];
		let type = pattern_types[part];
		if (type == TokenType.PLAIN) {
			if (prev_is_wildcard) {
				while (pos < format.length) {
					if (token == format[pos]) {
						let new_cur = cur.slice();
						this.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
					}
					pos++;
				}
			} else {
				if (token == format[pos]) {
					this.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
				}
			}
			return;
		} else if (type == TokenType.VARIABLE || type == TokenType.VARIABLE_WILDCARD) {
			if (prev_is_wildcard) {
				while (pos < format.length) {
					if (string_is_digit(format[pos])) {
						let new_cur = cur.slice();
						new_cur.push({
							format_pos: parseInt(format[pos], 10),
							pattern_part: part,
						});
						this.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
					}
					pos++;
				}
			} else {
				if (string_is_digit(format[pos])) {
					cur.push({
						format_pos: parseInt(format[pos]),
						pattern_part: part,
					});
					this.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
				}
			}
			return;
		} else if (type == TokenType.WILDCARD) {
			this.format_matches_pattern(format, pattern_parts, pattern_types, pos, part + 1, true, results, cur);
		} else if (type == TokenType.PLAIN_WILDCARD) {
			let front_is_wildcard = (token.charAt(0) == "*");
			let str = front_is_wildcard ? token.substring(1) : token.substring(0, token.length - 1);
			let lp = this;
			function fn() {
				if (string_matches_wildcard(front_is_wildcard, format[pos], str)) {
					let new_cur = cur.slice();
					lp.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
				} else if (string_is_digit(format[pos])) {
					let new_cur = cur.slice();
					new_cur.push({
						format_pos: parseInt(format[pos]),
						pattern_part: part,
					});
					lp.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
				}
			}
			if (prev_is_wildcard) {
				while (pos < format.length) {
					fn();
					pos++;
				}
			} else {
				fn();
			}
			return;
		} else {
			assert(false);
		}
	}

	parse_pattern(pattern) {
		let parts = string_split(pattern);
		let part_types = [];
		let number = /[0-9]/;
		for (let i = 0; i < parts.length; i++) {
			let str = parts[i];
			let wildcard = str.includes("*");
			if (number.test(str)) {
				part_types.push(wildcard ? TokenType.VARIABLE_WILDCARD : TokenType.VARIABLE);
			} else {
				if (wildcard) {
					part_types.push((str.length == 1) ? TokenType.WILDCARD : TokenType.PLAIN_WILDCARD);
				} else {
					part_types.push(TokenType.PLAIN);
				}
			}
		}
		let valid_variables = [];
		for (let i = 0; i < parts.length; i++) {
			valid_variables.push(new Set());
		}
		let wildcard_front_variables = {};
		let wildcard_back_variables = {};
		for (let i = 0; i < parts.length; i++) {
			if (part_types[i] == TokenType.VARIABLE) {
				let id = this.variable_ids[parts[i]];
				if (id == undefined) {
					return {
						valid: false,
						formats: null,
						variables: null,
					};
				}
				valid_variables[i].add(id);
			} else if (part_types[i] == TokenType.VARIABLE_WILDCARD || part_types[i] == TokenType.PLAIN_WILDCARD) {
				if (parts[i].charAt(0) == "*") {
					wildcard_front_variables[parts[i].substring(1)] = i;
				} else {
					wildcard_back_variables[parts[i].substring(0, parts[i].length - 1)] = i;
				}
			}
		}
		for (let i = 0; i < this.variables.length; i++) {
			let str = this.variables[i];
			for (let [ pattern, j ] of Object.entries(wildcard_front_variables)) {
				if (string_matches_wildcard(true, str, pattern)) {
					valid_variables[j].add(i);
				}
			}
			for (let [ pattern, j ] of Object.entries(wildcard_back_variables)) {
				if (string_matches_wildcard(false, str, pattern)) {
					valid_variables[j].add(i);
				}
			}
		}
		let valid_formats = {};
		for (let i = 0; i < this.formats.length; i++) {
			let f = this.formats[i];
			let format_parts = string_split(f);
			let results = [];
			let cur = [];
			this.format_matches_pattern(format_parts, parts, part_types, 0, 0, true, results, cur);
			if (results.length > 0) {
				valid_formats[i] = results;
			}
		}
		return {
			valid: true,
			formats: valid_formats,
			variables: valid_variables,
		};
	}

	search(threads, pattern, callback) {
		let parse = this.parse_pattern(pattern);
		if (!parse.valid) {
			callback([]);
			return;
		}
		let results = [];
		for (let i = 0; i < this.files.length; i++) {
			search_file(i, this, results, pattern, parse);
		}
		callback(results);
	}

	search_regex(threads, pattern, callback) {
		let re = new RegExp(pattern);
		let results = [];
		for (let i = 0; i < this.files.length; i++) {
			search_regex_file(i, this, results, re);
		}
		callback(results);
	}
};

function string_split(str) {
	let parts = [];
	let begin = 0;
	while (true) {
		while ((begin < str.length) && (str.charAt(begin) == " ")) {
			begin++;
		}
		if (begin == str.length) {
			break;
		}
		let end = str.indexOf(" ", begin);
		if (end < 0) {
			parts.push(str.substring(begin));
			break;
		}
		parts.push(str.substring(begin, end));
		begin = end + 1;
	}
	return parts;
}

function string_matches_wildcard(front_is_wildcard, str, pattern) {
	return (front_is_wildcard && str.endsWith(pattern)) || (!front_is_wildcard && str.startsWith(pattern));
}

function string_is_digit(str) {
	let ch = str.charCodeAt(0);
	return ("0".charCodeAt(0) <= ch) && (ch <= "9".charCodeAt(0));
}

function rebuild_line(log_parser, i, j) {
	let line = log_parser.file_tables[i][j];
	let parts = string_split(log_parser.formats[line.format_id]);
	let line_str = "";
	for (let k = 0; k < parts.length; k++) {
		if (k > 0) {
			line_str += " ";
		}
		let str = parts[k];
		if (string_is_digit(str)) {
			line_str += log_parser.variables[line.variables[parseInt(str, 10)]];
		} else {
			line_str += str;
		}
	}
	return line_str;
}

function process_file(i, lp, count, resolve) {
	let formats = [];
	let format_ids = {};
	let variables = [];
	let variable_ids = {};
	let table = [];

	let number = /[0-9]/;
	let space = / +/;

	let reader = readline.createInterface({
		input: fs.createReadStream(lp.files[i]),
	});
	let z = 0;
	let t = Date.now();
	reader.on("line", (line) => {
		/*
		z++;
		if (z % (10 * 1000) == 0) {
			let t2 = Date.now();
			console.log("[trace] process_file", i, "at", z, "lines", t2 - t, "ms.");
			t = t2;
		}
		*/
		let parts = string_split(line);
		let row = {
			format_id: null,
			variables: [],
		};
		let f = "";
		let n = 0;
		for (let i = 0; i < parts.length; i++) {
			let str = parts[i];
			if (i > 0) {
				f += " ";
			}
			if (number.test(str)) {
				let id = variable_ids[str];
				if (id == undefined) {
					id = variables.length;
					variables.push(str);
					variable_ids[str] = id;
				}
				row.variables.push(id);
				f += n.toString();
				n++;
			} else {
				f += str;
			}
		}
		let id = format_ids[f];
		if (id == undefined) {
			id = formats.length;
			formats.push(f);
			format_ids[f] = id;
		}
		row.format_id = id;
		table.push(row);
	});
	reader.on("close", () => {
		for (let j = 0; j < formats.length; j++) {
			let str = formats[j];
			let id = lp.format_ids[str];
			if (id == undefined) {
				id = lp.formats.length;
				lp.formats.push(str);
				lp.format_ids[str] = id;
			}
			format_ids[str] = id;
		}
		for (let j = 0; j < variables.length; j++) {
			let str = variables[j];
			let id = lp.variable_ids[str];
			if (id == undefined) {
				id = lp.variables.length;
				lp.variables.push(str);
				lp.variable_ids[str] = id;
			}
			variable_ids[str] = id;
		}
		for (let j = 0; j < table.length; j++) {
			let line = table[j];
			line.format_id = format_ids[formats[line.format_id]];
			for (let k = 0; k < line.variables.length; k++) {
				line.variables[k] = variable_ids[variables[line.variables[k]]];
			}
		}
		lp.file_tables[i] = table;
		count.value--;
		console.log("[trace] process_file", i, "done in", Date.now() - t, "ms,", count.value, "files remaining.");
		if (count.value == 0) {
			resolve(true);
		}
	});
}

function search_file(i, log_parser, results, pattern, parse) {
	let table = log_parser.file_tables[i];
	let t = Date.now();
	for (let j = 0; j < table.length; j++) {
		if (j % 1000 == 0) {
			let t2 = Date.now();
			console.log("[trace] search_file at", j, "lines", t2 - t, "ms.");
			t = t2;
		}
		let line = table[j];
		let pattern_variables = parse.formats[line.format_id];
		if (pattern_variables == undefined) {
			continue;
		}
		for (let k = 0; k < pattern_variables.length; k++) {
			let badness = false;
			for (let l = 0; l < pattern_variables[k].length; l++) {
				let pv = pattern_variables[k][l];
				let s = parse.variables[pv.pattern_part];
				if (!s.has(line.variables[pv.format_pos])) {
					badness = true;
					break;
				}
			}
			if (!badness) {
				results.push({
					file: i,
					line: j,
					str: rebuild_line(log_parser, i, j),
				});
				break;
			}
		}
	}
}

function search_regex_file(i, log_parser, results, pattern) {
	let table = log_parser.file_tables[i];
	for (let j = 0; j < table.length; j++) {
		let line = rebuild_line(log_parser, i, j);
		if (pattern.test(line)) {
			results.push({
				file: i,
				line: j,
				str: line,
			});
		}
	}
}

function print_results(results) {
	for (let i = 0; i < results.length; i++) {
		console.log("[found]", results[i].str);
	}
	console.log("[info]", results.length, "results.");
}

function main(args) {
	if (args.length < 2) {
		console.log("[usage] node log_parser.js <num threads> <file>");
		process.exit(1)
	}
	let num_threads = parseInt(args[0], 10);
	let files = [];
	let reader = readline.createInterface({
		input: fs.createReadStream(args[1]),
	});
	let p = new Promise((resolve, reject) => {
		reader.on("line", (line) => {
			files.push(line);
		});
		reader.on("close", () => {
			resolve(true);
		});
	});
	p.then((success) => {
		assert(success);
		let lp = new LogParser(files);
		let t0 = process.hrtime();
		lp.index(num_threads, () => {
			let t1 = process.hrtime();
			console.log("[info] indexing:", time_diff(t0, t1));
			/*
			lp.search(2, "INFO CoarseGrained* * 13*", (results) => {
				print_results(results);
			});
			lp.search_regex(2, "CoarseGrained.*13.*", (results) => {
				print_results(results);
			});
			*/
			t0 = process.hrtime();
			lp.search(num_threads, "INFO * org.apache.hadoop* * freed by fetcher#4", (results) => {
				t1 = process.hrtime();
				console.log("[info] indexed search:", time_diff(t0, t1));
				print_results(results);
				t0 = process.hrtime();
				lp.search_regex(num_threads, "INFO.*freed by fetcher#\\d in [1-5]+ms", (results) => {
					t1 = process.hrtime();
					console.log("[info] regex search:", time_diff(t0, t1));
					print_results(results);
				});
			});
		});
	}).catch((reason) => {
		console.log("[error]", reason);
	});
}

if (!module.parent) {
	main(process.argv.slice(2));
}
