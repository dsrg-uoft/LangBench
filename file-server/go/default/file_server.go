package main

import "os"
import "net"
//import "fmt"
import "bufio"
import "strings"
import "strconv"
import "io/ioutil"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

func build_header(code int, body string) string {
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
	res += "Content-Length: " + strconv.Itoa(len(body)) + "\r\n"
	res += "\r\n"
	return res
}

func read_file(path string, dir string) *string {
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
	data, err := ioutil.ReadFile(filtered)
	if err != nil {
		return nil
	}
	var ret *string = new(string)
	*ret = string(data)
	return ret
}

func handle_client(conn *net.Conn, dir string) {
	defer (*conn).Close()
	var reader *bufio.Reader = bufio.NewReader(*conn)
	line, err := reader.ReadString('\n')
	assert(err == nil)
	line = strings.TrimSuffix(line, "\r\n")
	var parts []string = strings.Split(line, " ")
	var path string = parts[1]
	var data *string = read_file(path, dir)
	var header string
	if data == nil {
		data = new(string)
		*data = "Not found."
		header = build_header(404, *data)
	} else {
		header = build_header(200, *data)
	}
	(*conn).Write([]byte(header))
	(*conn).Write([]byte(*data))
	//print("[trace] closing connection.\n")
}

func main() {
	server, err := net.Listen("tcp", os.Args[1] + ":" + os.Args[2])
	assert(err == nil)
	defer server.Close()

	for {
		conn, err := server.Accept()
		assert(err == nil)
		//fmt.Printf("[info] new connection.\n")
		go handle_client(&conn, os.Args[3])
	}
}
