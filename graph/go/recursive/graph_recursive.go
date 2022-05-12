package main

import "os"
import "fmt"
import "math"
import "bufio"
import "strings"
import "strconv"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

var iterations int = 0

type Vertex struct {
	next *Vertex
	prev *Vertex
	colour *int
	neighbours map[*Vertex]bool
}

type Graph struct {
	dummy *Vertex
	size int
}

type vertex_pair struct {
	start *Vertex
	sibling *Vertex
}

type vertex_colour_colour struct {
	v *Vertex
	i int
	j int
}

func magic_f(k int, n int) float64 {
	return math.Ceil(math.Pow(float64(n), 1.0 - (1.0 / float64(k - 1))))
}

func k_ge_log_n(k int, n int) bool {
	var x int64 = 1
	for i := 0; i < k; i++ {
		x *= 2
	}
	return x >= int64(n)
}

func newVertex(colour *int) *Vertex {
	var v *Vertex = new(Vertex)
	v.next = nil
	v.prev = nil
	v.colour = colour
	v.neighbours = make(map[*Vertex]bool)
	return v
}

func (this *Vertex) degree() int {
	return len(this.neighbours)
}

func (this *Vertex) sudoku() {
	this.prev.next = this.next
	if this.next != nil {
		this.next.prev = this.prev
	}
	for v, _ := range this.neighbours {
		delete(v.neighbours, this)
	}
}

func (this *Vertex) induce() Graph {
	var induced Graph = newGraph()
	var m map[*Vertex]*Vertex = make(map[*Vertex]*Vertex)
	graph_explore_recursive(this, &induced, m, &this.neighbours)
	return induced
}

func newGraph() Graph {
	var g Graph
	g.dummy = newVertex(nil)
	g.size = 0
	return g
}

func (this *Graph) head() *Vertex {
	return this.dummy.next
}

func (this *Graph) shift(v *Vertex) {
	var h *Vertex = this.head()
	if h != nil {
		v.next = h
		v.prev = this.dummy
		h.prev = v
	}
	this.dummy.next = v
	this.size++
}

func (this *Graph) duplicate() Graph {
	var dup Graph = newGraph()
	var m map[*Vertex]*Vertex = make(map[*Vertex]*Vertex)
	for v := this.head(); v != nil; v = v.next {
		graph_explore_recursive(v, &dup, m, nil)
	}
	return dup
}

func (this *Graph) social_credit(bad *Vertex) {
	bad.sudoku()
	this.size--
	for v, _ := range bad.neighbours {
		v.sudoku()
		this.size--
	}
}

func (this *Graph) verify_colouring() bool {
	for v := this.head(); v != nil; v = v.next {
		if *v.colour == 0 {
			return false
		}
		for u, _ := range v.neighbours {
			if *v.colour == *u.colour {
				return false
			}
		}
	}
	return true
}

func (this *Graph) find_max_degree_vertex() *Vertex {
	var d int = 0
	var ret *Vertex = nil
	for v := this.head(); v != nil; v = v.next {
		var e int = v.degree()
		if e > d {
			ret = v
			d = e
		}
	}
	return ret
}

func (this *Graph) colour_2(i int, j int) bool {
	for v := this.head(); v != nil; v = v.next {
		if *v.colour != 0 {
			continue
		}
		if !graph_colour_2_helper_recursive(v, i, j) {
			return false
		}
	}
	return true
}

func (this *Graph) colour_b(k int, i int) int {
	if k == 2 {
		if this.colour_2(i, i + 1) {
			return 2
		}
		return 0
	}
	var n int = this.size
	if k_ge_log_n(k, n) {
		var j int = 0
		for v := this.head(); v != nil; v = v.next {
			*v.colour = i + j
			j++
		}
		return n
	}
	for {
		var v *Vertex = this.find_max_degree_vertex()
		if float64(v.degree()) < magic_f(k, n) {
			break
		}
		var h Graph = v.induce()
		var j int = h.colour_b(k - 1, i)
		if j == 0 {
			return 0
		}
		i += j
		*v.colour = i
		this.social_credit(v)
	}
	var max_degree int = 0
	var max_colour int = 0
	for v := this.head(); v != nil; v = v.next {
		var seen map[int]bool = make(map[int]bool)
		for e, _ := range v.neighbours {
			seen[*e.colour] = true
		}
		if max_degree < v.degree() {
			max_degree = v.degree()
		}
		var j int = i
		for {
			_, ok := seen[j]
			if !ok {
				*v.colour = j
				if max_colour < j {
					max_colour = j
				}
				j++
				break

			}
			j++
		}
	}
	assert(max_colour < max_degree + i + 1)
	var ret int = max_colour - i + 1
	var bound float64 = 2.0 * float64(k) * magic_f(k, n)
	if float64(ret) > bound {
		return 0
	}
	return ret
}

func (this *Graph) colour_c() int {
	var i uint = 1
	for {
		var h Graph = this.duplicate()
		if h.colour_b(1 << i, 1) != 0 {
			break
		}
		i++
	}
	var l int = (1 << (i - 1)) + 1
	var r int = 1 << i
	for l < r {
		var m int = (l + r) / 2
		var h Graph = this.duplicate()
		if h.colour_b(m, 1) == 0 {
			l = m + 1
		} else {
			r = m
		}
	}
	var h Graph = this.duplicate()
	var k int = h.colour_b(l, 1)
	assert(k != 0)
	return k
}

func graph_explore_recursive(start *Vertex, g *Graph, m map[*Vertex]*Vertex, valid *map[*Vertex]bool) *Vertex {
	new_vertex, ok := m[start]
	if ok {
		return new_vertex
	}
	new_vertex = newVertex(start.colour)
	*new_vertex.colour = 0
	m[start] = new_vertex
	for v, _ := range start.neighbours {
		if valid != nil {
			_, ok := (*valid)[v]
			if !ok {
				continue
			}
		}
		var neighbour *Vertex = graph_explore_recursive(v, g, m, valid)
		new_vertex.neighbours[neighbour] = true
	}
	g.shift(new_vertex)
	return new_vertex
}

func graph_colour_2_helper_recursive(v *Vertex, i int, j int) bool {
	if *v.colour == j {
		return false
	}
	if *v.colour == 0 {
		*v.colour = i
		for u, _ := range v.neighbours {
			if !graph_colour_2_helper_recursive(u, j, i) {
				return false
			}
		}
	}
	return true
}

func graph_from_file(path string) Graph {
	var g Graph = newGraph()
	file, err := os.Open(path)
	assert(err == nil)
	defer file.Close()
	var m map[int]*Vertex = make(map[int]*Vertex)
	var scanner *bufio.Scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		var line string = scanner.Text()
		if line[0] == '#' {
			continue
		}
		var parts []string = strings.Split(line, "\t")
		x, err := strconv.Atoi(parts[0])
		assert(err == nil)
		y, err := strconv.Atoi(parts[1])
		assert(err == nil)
		vx, ok := m[x]
		if !ok {
			vx = newVertex(new(int))
			m[x] = vx
			g.shift(vx)
		}
		vy, ok := m[y]
		if !ok {
			vy = newVertex(new(int))
			m[y] = vy
			g.shift(vy)
		}
		vx.neighbours[vy] = true
		vy.neighbours[vx] = true
	}
	return g
}

func main() {
	var g Graph = graph_from_file(os.Args[1])
	var k int = g.colour_c()
	fmt.Printf("k = %d\n", k)
	assert(g.verify_colouring())
}
