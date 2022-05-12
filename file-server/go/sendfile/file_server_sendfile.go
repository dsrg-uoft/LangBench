package main

import "os"
import "net"
import "bufio"
import "strings"
import "strconv"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

func build_header(code int, length int) string {
	var status string
	if code == 200 {
		status = "OK"
	} else if code == 404 {
		status = "Not Found"
	} else {
		assert(false)
	}
	var res string = "HTTP/1.0 " + strconv.Itoa(code) + " " + status + "\r\n"
	res += "Content-Type: text/plain; charset=UTF-8\r\n"
	res += "Content-Length: " + strconv.Itoa(length) + "\r\n"
	res += "\r\n"
	return res
}

func read_file(path string, dir string) *os.File {
	var parts []string = strings.Split(path, "/")
	var filtered string = ""
	for i := 1; i < len(parts); i++ {
		var p string = parts[i]
		if p == ".." {
			continue
		}
		filtered += "/" + p
	}
	filtered = dir + filtered
	f, err := os.Open(filtered)
	if err != nil {
		return nil
	}
	return f
}

func handle_client(conn *net.TCPConn, dir string) {
	defer (*conn).Close()
	var reader *bufio.Reader = bufio.NewReader(conn)
	line, err := reader.ReadString('\n')
	assert(err == nil)
	line = strings.TrimSuffix(line, "\r\n")
	var parts []string = strings.Split(line, " ")
	var path string = parts[1]
	var data *os.File = read_file(path, dir)
	var header string
	if data == nil {
		var body string = "Not found."
		header = build_header(404, len(body))
		(*conn).Write([]byte(header))
		(*conn).Write([]byte(body))
	} else {
		fi, err := data.Stat()
		assert(err == nil)
		header = build_header(200, int(fi.Size()))
		(*conn).Write([]byte(header))
		(*conn).ReadFrom(data)
	}
	//print("[trace] closing connection.\n")
}

func main() {
	//server, err := net.Listen("tcp", os.Args[1] + ":" + os.Args[2])
	addr, err := net.ResolveTCPAddr("tcp", os.Args[1] + ":" + os.Args[2])
	assert(err == nil)
	server, err := net.ListenTCP("tcp", addr)
	assert(err == nil)
	defer server.Close()

	for {
		conn, err := server.AcceptTCP()
		assert(err == nil)
		//fmt.Printf("[info] new connection.\n")
		go handle_client(conn, os.Args[3])
	}
}
