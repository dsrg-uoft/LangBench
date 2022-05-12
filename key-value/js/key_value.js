

const HashMap = require("./hashmap.js");
const net = require("net");
const readline = require("readline");

class SocketStream {
	constructor(socket) {
		this.socket = socket;
		this.socket.setEncoding("utf8");
		this.buffer = [];
		this.callback = null;
		let rl = readline.createInterface({
			input: socket,
			crlfDelay: Infinity,
		});
		let ss = this;
		rl.on("line", function (line) {
			line = line.substr(0, line.length - 2);
			if (ss.callback != null) {
				console.assert(ss.buffer.length == 0);
				let fn = ss.callback;
				ss.callback = null;
				fn(line);
				return;
			}
			ss.buffer.push(line);
		});
	}

	read_line(callback) {
		console.assert(this.callback == null);
		if (this.buffer.length == 0) {
			this.callback = callback;
			return;
		}
		let line = this.buffer.shift();
		callback(line);
		return;
	}
}

function process_command(arr, socket, map) {
	let ret = null;
	if (arr[0] == "GET") {
		let val = map.op_get(arr[1]);
		if (val == null) {
			ret = "$-1\r\n";
		} else {
			ret = "$" + val.length.toString() + "\r\n" + val + "\r\n";
		}
	} else if (arr[0] == "SET") {
		map.op_set(arr[1], arr[2]);
		ret = "+OK\r\n";
	} else {
		console.log("[info] unknown command", arr);
		return;
	}
	//console.log("[trace] command", arr, "returning", ret);
	socket.write(ret);
}

function main(args) {
	let map = new HashMap(parseInt(args[2], 10) * 1024, parseInt(args[3], 10));
	net.createServer(function (socket) {
		console.log("[info] new connection.");
		socket.setEncoding("utf8");
		socket.on("end", function () {
			console.log("[info] closing connection.");
		});
		let rl = readline.createInterface({
			input: socket,
			crlfDelay: Infinity,
		});
		let state = 0;
		let array_len = -1;
		let array_elem = [];
		let str_len = -1;
		rl.on("line", function (line) {
			if (state == 0) {
				console.assert(line.charAt(0) == '*');
				array_len = parseInt(line.substr(1), 10);
				state = 1;
			} else if (state == 1) {
				console.assert(line.charAt(0) == '$');
				str_len = parseInt(line.substr(1), 10);
				state = 2;
			} else if (state == 2) {
				console.assert(line.length == str_len);
				array_elem.push(line);
				if (array_elem.length < array_len) {
					state = 1;
				} else {
					process_command(array_elem, socket, map);
					array_elem = [];
					state = 0;
				}
			}
		});

	}).listen(parseInt(args[1], 10), args[0]);
	//}).listen(parseInt(args[0], 10), "127.0.0.1");
}

if (!module.parent) {
	main(process.argv.slice(2));
}
