

const net = require("net");
const readline = require("readline");
const fs = require("fs");
const worker = require("worker_threads");

function assert(cond) {
	if (!cond) {
		throw new RuntimeException("badness");
	}
}

function build_header(code, body) {
	let stat = null;
	if (code == 200) {
		stat = "OK";
	} else if (code == 404) {
		stat = "Not Found";
	} else {
		assert(false);
	}
	let res = "HTTP/1.0 " + code + " " + stat + "\r\n";
	res += "Content-Type: text/plain; charset=UTF-8\r\n";
	res += "Content-Length: " + body.length + "\r\n";
	res += "\r\n";
	return res;
}

function read_file(path, directory, callback) {
	let parts = path.split("/");
	let filtered = "";
	for (let i = 1; i < parts.length; i++) {
		let p = parts[i];
		if (p == "..") {
			continue;
		}
		filtered += "/" + p;
	}
	filtered = directory + filtered
	fs.readFile(filtered, null, (err, data) => {
		if (err == null) {
			callback(data);
		} else {
			callback(null);
		}
	});
}

function handle_client(conn, line, directory) {
	let parts = line.split(" ");
	let path = parts[1];
	read_file(path, directory, (data) => {
		let header = null;
		if (data == null) {
			data = Buffer.from("Not found.", "ascii");
			header = build_header(404, data);
		} else {
			header = build_header(200, data);
		}
		conn.write(header, "ascii");
		conn.write(data);
	});
}

function main(args) {
	net.createServer((socket) => {
		let w = new worker.Worker(__filename, {
			workerData: socket,
		});
		let rl = readline.createInterface({
			input: socket,
			crlfDelay: Infinity,
		});
		rl.once("line", (line) => {
			handle_client(socket, line, args[1]);
		});
	}).listen(parseInt(args[1], 10), args[0]);
	//}).listen(parseInt(args[0], 10), "127.0.0.1");
}

if (!module.parent) {
	main(process.argv.slice(2));
}
