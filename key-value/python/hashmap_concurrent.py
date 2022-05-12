

import time
import random
import math
import threading
import contextlib
from typing import List

class AtomicInteger:
	def __init__(self):
		self.value: int = 0
		self.lock: threading.Lock = threading.Lock()

	def add(self, x: int) -> None:
		self.lock.acquire()
		self.value += x
		self.lock.release()

	def get(self) -> int:
		self.lock.acquire()
		x: int = self.value
		self.lock.release()
		return x

class RWLock:
	def __init__(self):
		self.read_lock_: threading.Lock = threading.Lock()
		self.write_lock_: threading.Lock = threading.Lock()
		self.num_readers: int = 0

	def read_acquire(self):
		self.read_lock_.acquire()
		if self.num_readers == 0:
			self.write_lock_.acquire()
		self.num_readers += 1
		self.read_lock_.release()

	def read_release(self):
		self.read_lock_.acquire()
		self.num_readers -= 1
		if self.num_readers == 0:
			self.write_lock_.release()
		self.read_lock_.release()

	def write_acquire(self):
		self.write_lock_.acquire()

	def write_release(self):
		self.write_lock_.release()

	@contextlib.contextmanager
	def read_lock(self):
		try:
			self.read_acquire()
			yield
		finally:
			self.read_release()

	@contextlib.contextmanager
	def write_lock(self):
		try:
			self.read_acquire()
			yield
		finally:
			self.read_release()

class Slot:
	def __init__(self, key: str, value: str, next_: "Slot") -> None:
		self.key: str = key
		self.value: str = value
		self.timestamp: float = time.time()
		self.next_: "Slot" = next_

	def set(self, value: str) -> None:
		self.value = value
		self.timestamp = time.time()

	def get(self) -> str:
		self.timestamp = time.time()
		return self.value

class Row:
	def __init__(self):
		self.head: Slot = None
		self.lock: RWLock = RWLock()

class EvictionPoolEntry:
	def __init__(self, s: Slot) -> None:
		self.key: str = s.key
		self.timestamp: float = s.timestamp

class EvictionPool:
	MAX_LENGTH: int = 16
	CANDIDATE_COUNT: int = 5

	def __init__(self, hashmap: "HashMap") -> None:
		self.hashmap: "HashMap" = hashmap
		self.pool: List[EvictionPoolEntry] = [None] * EvictionPool.MAX_LENGTH
		random.seed(322)
		self.lock: threading.Lock = threading.Lock()

	def populate(self) -> None:
		self.lock.acquire()
		try:
			candidates: List[Slot] = [None] * EvictionPool.CANDIDATE_COUNT
			i: int = 0
			while i < len(candidates):
				row: int = math.floor(random.random() * len(self.hashmap.rows))
				with self.hashmap.rows[row].lock.read_lock():
					s: Slot = self.hashmap.rows[row].head
					while s != None and i < len(candidates):
						candidates[i] = s
						i += 1
						s = s.next_

			for candidate in candidates:
				for j in range(len(self.pool)):
					if self.pool[j] == None:
						self.pool[j] = EvictionPoolEntry(candidate)
						break
					elif self.pool[j].timestamp < candidate.timestamp:
						self.pool[j + 1:] = self.pool[j:-1]
						self.pool[j] = EvictionPoolEntry(candidate)
						break
		finally:
			self.lock.release()

	def pop(self) -> str:
		self.lock.acquire()
		try:
			k: str = None
			if self.pool[0] != None:
				k = self.pool[0].key
				self.pool[:] = self.pool[1:] + [None]
			return k
		finally:
			self.lock.release()


class HashMap:
	CANDIDATE_COUNT: int = 5

	def __init__(self, max_size: int, num_rows: int) -> None:
		self.rows: List[Row] = [None] * num_rows
		for i in range(len(self.rows)):
			self.rows[i] = Row()
		self.size: AtomicInteger = AtomicInteger()
		# self.eviction_pool: EvictionPool = EvictionPool(self)
		random.seed(322)
		self.max_size: int = max_size

	@staticmethod
	def hash(s: str) -> int:
		h: int = 0
		for i in range(len(s)):
			h = (h * 31) + ord(s[i])
		return h

	def get_row(self, s: str) -> int:
		return HashMap.hash(s) % len(self.rows)

	def find(self, key: str, i: int) -> Slot:
		s: Slot = self.rows[i].head
		while s != None:
			if s.key == key:
				return s
			s = s.next_
		return None

	def exists(self, key: str) -> bool:
		s: Slot = None
		i: int = self.get_row(key)
		with self.rows[i].lock.read_lock():
			s = self.find(key, i)
		return s is not None

	def get(self, key: str) -> str:
		i: int = self.get_row(key)
		with self.rows[i].lock.read_lock():
			s: Slot = self.find(key, i)
			if s is None:
				return None
			return s.get()

	def set(self, key: str, value: str) -> int:
		if self.size.get() > self.max_size:
			self.evict()

		i: int = self.get_row(key)
		with self.rows[i].lock.write_lock():
			s: Slot = self.find(key, i)
			if s != None:
				self.size.add(len(value) - len(s.value))
				s.set(value)
				return 1

			self.size.add(len(value))
			s = Slot(key, value, self.rows[i].head)
			self.rows[i].head = s
			return 0

	class DelPair:
		def __init__(self) -> None:
			self.keys: int = 0
			self.size: int = 0

	def delete(self, key: str) -> "HashMap.DelPair":
		ret: "HashMap.DelPair" = HashMap.DelPair()
		i: int = HashMap.hash(key) % len(self.rows)
		with self.rows[i].lock.write_lock():
			prev: Slot = None
			s: Slot = self.rows[i].head
			while s != None:
				if s.key == key:
					if prev == None:
						self.rows[i].head = s.next_
					else:
						prev.next_ = s.next_
					ret.keys += 1
					ret.size = len(s.value)
					self.size.add(-ret.size)
					break
				prev = s
				s = s.next_
		return ret

	def sample(self) -> str:
		key: str = None
		oldest: int = 0
		i: int = 0
		while i < HashMap.CANDIDATE_COUNT:
			row: int = math.floor(random.random() * len(self.rows))
			with self.rows[row].lock.read_lock():
				s: Slot = self.rows[row].head
				while s != None and i < HashMap.CANDIDATE_COUNT:
					if oldest == 0 or oldest > s.timestamp:
						key = s.key
						oldest = s.timestamp
					i += 1
					s = s.next_
		return key

	def evict(self) -> int:
		size_freed: int = 0
		while self.size.get() > self.max_size:
			key: str = self.sample()
			size_freed += self.delete(key).size
		return size_freed
