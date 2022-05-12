package main

import "os"
import "fmt"
import "net"
import "bufio"
import "strconv"
import "strings"
import "io"

func handle_connection(hashmap *HashMap, conn *net.Conn) {
	defer (*conn).Close()
	var reader *bufio.Reader = bufio.NewReader(*conn)
	for {
		buf, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				break
			}
			fmt.Printf("[error] unable to read full array %v.\n", err)
			assert(false)
		}
		buf = strings.TrimSuffix(buf, "\r\n")
		assert(buf[0] == '*')
		cmd_len, err := strconv.Atoi(buf[1:])
		assert(err == nil)
		var parts []string = make([]string, cmd_len)
		for i := 0; i < cmd_len; i++ {
			buf, err = reader.ReadString('\n')
			buf = strings.TrimSuffix(buf, "\r\n")
			assert(err == nil)
			assert(buf[0] == '$')
			buf, err = reader.ReadString('\n')
			buf = strings.TrimSuffix(buf, "\r\n")
			assert(err == nil)
			parts[i] = buf
		}

		var ret string
		if parts[0] == "GET" {
			var val *string = hashmap.Get(parts[1])
			if val == nil {
				ret = "$-1\r\n"
			} else {
				ret = "$" + strconv.Itoa(len(*val)) + "\r\n" + *val + "\r\n"
			}
		} else if parts[0] == "SET" {
			hashmap.Set(parts[1], parts[2])
			ret = "+OK\r\n"
		} else {
			fmt.Printf("[info] unknown command %s.\n", parts[0])
			break
		}
		(*conn).Write([]byte(ret))
		//fmt.Printf("[info] cmd: %v ret: %v\n", parts, ret);
	}
	fmt.Printf("[info] closing connection.\n")
}

func main() {
	if len(os.Args) <= 4 {
		fmt.Printf("[info] usage: ./server <ip> <port> <size> <rows>\n")
		os.Exit(1)
	}
	size, err := strconv.Atoi(os.Args[3])
	assert(err == nil)
	rows, err := strconv.Atoi(os.Args[4])
	assert(err == nil)

	server, err := net.Listen("tcp", os.Args[1] + ":" + os.Args[2])
	assert(err == nil)
	defer server.Close()

	var hashmap *HashMap = NewHashMap(int64(size) * 1024, rows)
	for {
		conn, err := server.Accept()
		assert(err == nil)
		fmt.Printf("[info] new connection.\n")

		go handle_connection(hashmap, &conn)
	}
}
