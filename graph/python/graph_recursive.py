#!/usr/bin/env python3

import sys
import math
import resource
import time
from typing import Set, Dict, List, Generator, Tuple, Callable

iterations: int = 0

class Colour:
	def __init__(self: "Colour") -> None:
		self.value: int = 0

class Vertex:
	def __init__(self: "Vertex", colour: Colour = None) -> None:
		self.next: Vertex = None
		self.prev: Vertex = None
		self.colour: Colour = Colour() if colour is None else colour
		self.neighbours: Set[Vertex] = set()

	def degree(self: "Vertex") -> int:
		return len(self.neighbours)

	def sudoku(self: "Vertex") -> None:
		self.prev.next = self.next
		if self.next is not None:
			self.next.prev = self.prev
		v: Vertex
		for v in self.neighbours:
			v.neighbours.remove(self)

	def induce(self: "Vertex") -> "Graph":
		induced: Graph = Graph()
		m: Dict[Vertex, Vertex] = {}
		#Graph.explore(self, induced, m, self.neighbours, time.time())
		Graph.explore(self, induced, m, self.neighbours, None)
		return induced

class Graph:
	EXPLORE: Callable[[Vertex, "Graph", Dict[Vertex, Vertex], Set[Vertex], float], Vertex] = None
	COLOUR_2_HELPER: Callable[[Vertex, int, int], bool] = None

	"""
	@staticmethod
	def initialize():
		Graph.EXPLORE = Graph.explore
		#Graph.EXPLORE = Graph.explore_iterative
		Graph.COLOUR_2_HELPER = Graph.colour_2_helper
		#Graph.COLOUR_2_HELPER = Graph.colour_2_helper_iterative
	"""

	def __init__(self: "Graph") -> None:
		self.dummy: Vertex = Vertex()
		self.dummy.colour = None
		self.size: int = 0
		self.loop_time: float = 0
		self.loop_count: int = 0
		self.stack_time: float = 0
		self.stack_count: int = 0
		self.call_time: float = 0
		self.call_count: int = 0

	def head(self: "Graph") -> Vertex:
		return self.dummy.next

	def vertices(self: "Graph") -> Generator[Vertex, None, None]:
		v: Vertex = self.head()
		while v is not None:
			yield v
			v = v.next

	def shift(self: "Graph", v: Vertex) -> None:
		h: Vertex = self.head()
		if h is not None:
			v.next = h
			v.prev = self.dummy
			h.prev = v
		self.dummy.next = v
		self.size += 1

	def duplicate(self: "Graph") -> "Graph":
		dup: Graph = Graph()
		m: Dict[Vertex, Vertex] = {}
		v: Vertex
		for v in self.vertices():
			#Graph.explore(v, dup, m, None, time.time())
			Graph.explore(v, dup, m, None, None)
		"""
		print("[debug] loop: {:.3f} / {} = {:.3f}, stack: {:.3f} / {} = {:.3f}, call: {:.3f} / {} = {:.3f}".format(
			dup.loop_time,
			dup.loop_count,
			dup.loop_time / (1 if dup.loop_count == 0 else dup.loop_count),
			dup.stack_time,
			dup.stack_count,
			dup.stack_time / (1 if dup.stack_count == 0 else dup.stack_count),
			dup.call_time,
			dup.call_count,
			dup.call_time / (1 if dup.call_count == 0 else dup.call_count),
		))
		"""
		return dup

	@staticmethod
	def explore(start: Vertex, g: "Graph", m: Dict[Vertex, Vertex], valid: Set[Vertex], t_out: float) -> Vertex:
		#t_in: float = time.time()
		#g.call_time += t_in - t_out
		#g.call_count += 1
		new_vertex: Vertex = m.get(start)
		if new_vertex is not None:
			return new_vertex
		new_vertex = Vertex(start.colour)
		start.colour.value = 0
		m[start] = new_vertex
		v: Vertex
		for v in start.neighbours:
			if (valid is not None) and (v not in valid):
				continue
			#neighbour: Vertex = Graph.explore(v, g, m, valid, time.time())
			neighbour: Vertex = Graph.explore(v, g, m, valid, None)
			new_vertex.neighbours.add(neighbour)
		g.shift(new_vertex)
		return new_vertex

	@staticmethod
	def explore_iterative(start: Vertex, g: "Graph", m: Dict[Vertex, Vertex], valid: Set[Vertex], t_out: float) -> None:
		global iterations
		stack: List[Tuple[Vertex, Vertex]] = []
		stack.append((start, None))
		t0: float = time.time()
		while len(stack) > 0:
			iterations += 1
			t1: float = time.time()
			g.loop_time += t1 - t0
			g.loop_count += 1
			sibling: Vertex
			t0 = time.time()
			start, sibling = stack.pop()
			t1 = time.time()
			g.stack_time += t1 - t0
			g.stack_count += 1
			new_vertex: Vertex = m.get(start)
			if new_vertex is not None:
				if sibling is not None:
					sibling.neighbours.add(new_vertex)
				t0 = time.time()
				continue
			new_vertex = Vertex(start.colour)
			start.colour.value = 0
			m[start] = new_vertex
			v: Vertex
			for v in start.neighbours:
				if (valid is not None) and (v not in valid):
					continue
				t0 = time.time()
				stack.append((v, new_vertex))
				t1 = time.time()
				g.stack_time += t1 - t0
				g.stack_count += 1
			g.shift(new_vertex)
			if sibling is not None:
				sibling.neighbours.add(new_vertex)
			t0 = time.time()

	def social_credit(self: "Graph", bad: Vertex) -> None:
		bad.sudoku()
		self.size -= 1
		v: Vertex
		for v in bad.neighbours:
			v.sudoku()
			self.size -= 1

	def verify_colouring(self: "Graph") -> bool:
		v: Vertex
		for v in self.vertices():
			if v.colour.value == 0:
				return False
			u: Vertex
			for u in v.neighbours:
				if v.colour.value == u.colour.value:
					return False
		return True

	def find_max_degree_vertex(self: "Graph") -> Vertex:
		d: int = 0
		ret: Vertex = None
		v: Vertex
		for v in self.vertices():
			e = v.degree()
			if e > d:
				ret = v
				d = e
		return ret

	@staticmethod
	def magic_f(k: int, n: int) -> float:
		return math.ceil(math.pow(n, 1 - (1.0 / (k - 1))))

	@staticmethod
	def k_ge_log_n(k: int, n: int) -> bool:
		return 2 ** k >= n

	def colour_2(self: "Graph", i: int, j: int) -> bool:
		v: Vertex
		for v in self.vertices():
			if v.colour.value != 0:
				continue
			if not Graph.colour_2_helper(v, i, j):
				return False
		return True

	@staticmethod
	def colour_2_helper(v: Vertex, i: int, j: int) -> bool:
		if v.colour.value == j:
			return False
		if v.colour.value == 0:
			v.colour.value = i
			u: Vertex
			for u in v.neighbours:
				if not Graph.colour_2_helper(u, j, i):
					return False
		return True

	@staticmethod
	def colour_2_helper_iterative(v: Vertex, i: int, j: int) -> bool:
		stack: List[Tuple[Vertex, int, int]] = []
		stack.append((v, i, j))
		while len(stack) > 0:
			v, i, j = stack.pop()
			if v.colour.value == j:
				return False
			if v.colour.value == 0:
				v.colour.value = i
				u: Vertex
				for u in v.neighbours:
					stack.append((u, j, i))
		return True

	def colour_b(self: "Graph", k: int, i: int) -> int:
		if k == 2:
			if self.colour_2(i, i + 1):
				#print("B: k = " + str(k) + " ret = 2")
				return 2
			#print("B: k = " + str(k) + " ret = 0")
			return 0
		n: int = self.size
		if Graph.k_ge_log_n(k, n):
			j: int = 0
			v: Vertex
			for v in self.vertices():
				v.colour.value = i + j
				j += 1
			#print('B: k = ' + str(k) + ' ret = ' + str(n))
			return n
		while True:
			v = self.find_max_degree_vertex()
			if v.degree() < Graph.magic_f(k, n):
				#print("- breaking k = {} degree = {} magic = {}".format(k, v.degree(), Graph.magic_f(k, n)));
				break
			"""
			if v.degree() < (k * k):
				break
			"""
			h: Graph = v.induce()
			j = h.colour_b(k - 1, i)
			if j == 0:
				#print("B: k = " + str(k) + " ret = 0")
				return 0
			i += j
			v.colour.value = i
			self.social_credit(v)
		max_degree: int = 0
		max_colour: int = 0
		for v in self.vertices():
			seen: Set[int] = set()
			e: Vertex
			for e in v.neighbours:
				seen.add(e.colour.value)
			if max_degree < v.degree():
				max_degree = v.degree()
			j = i
			while True:
				if j not in seen:
					v.colour.value = j
					if max_colour < j:
						max_colour = j
					j += 1
					break
				j += 1
		assert(max_colour < max_degree + i + 1)

		ret: int = max_colour - i + 1
		bound: float = 2 * k * Graph.magic_f(k, n)
		#print("Bend: k = {}, ret = {}, bound = {}".format(k, ret, bound))
		return 0 if ret > bound else ret

	def colour_c(self: "Graph") -> int:
		i: int = 1
		while self.duplicate().colour_b(1 << i, 1) == 0:
			i += 1
		#print("C: i = " + str(i))

		l: int = (1 << (i - 1)) + 1
		r: int = 1 << i
		while l < r:
			m: int = (l + r) // 2
			if self.duplicate().colour_b(m, 1) == 0:
				l = m + 1
			else:
				r = m
		k: int = self.duplicate().colour_b(l, 1)
		assert(k != 0)
		return k

	@staticmethod
	def from_file(path: str) -> "Graph":
		g: Graph = Graph()
		with open(path, encoding = 'utf-8') as f:
			m: Dict[int, Vertex] = {}
			for line in f:
				if line.startswith('#'):
					continue
				parts: List[str] = line.split()
				x: int = int(parts[0])
				y: int = int(parts[1])
				vx: Vertex = m.get(x)
				if vx is None:
					vx = Vertex()
					m[x] = vx
					g.shift(vx)
				vy: Vertex = m.get(y)
				if vy is None:
					vy = Vertex()
					m[y] = vy
					g.shift(vy)
				vx.neighbours.add(vy)
				vy.neighbours.add(vx)
		return g

def main(args: List[str]) -> None:
	sys.setrecursionlimit(1000 * 1000)
	resource.setrlimit(resource.RLIMIT_STACK, (128 * 1024 * 1024, resource.RLIM_INFINITY))
	#Graph.initialize()
	g: Graph = Graph.from_file(args[0])
	k: int = g.colour_c()
	print("k = " + str(k))
	print("iterations = " + str(iterations))
	assert(g.verify_colouring())

if __name__ == '__main__':
	main(sys.argv[1:])
