

import time
import random
import math
from typing import List

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

class PairSlotIndex:
	def __init__(self, s: Slot, i: int) -> None:
		self.slot: Slot = s
		self.index: int = i

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

	def populate(self) -> None:
		candidates: List[Slot] = [None] * EvictionPool.CANDIDATE_COUNT
		i: int = 0
		while i < len(candidates):
			row: int = math.floor(random.random() * len(self.hashmap.rows))
			s: Slot = self.hashmap.rows[row]
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

	def pop(self) -> str:
		k: str = None
		if self.pool[0] != None:
			k = self.pool[0].key
			self.pool[:] = self.pool[1:] + [None]
		return k


class HashMap:
	CANDIDATE_COUNT: int = 5

	def __init__(self, max_size: int, num_rows: int) -> None:
		self.rows: List[Slot] = [None] * num_rows
		self.size: int = 0
		self.eviction_pool: EvictionPool = EvictionPool(self)
		self.max_size: int = max_size

	@staticmethod
	def hash(s: str) -> int:
		h: int = 0
		for i in range(len(s)):
			h = (h * 31) + ord(s[i])
		return h

	def find(self, key: str) -> PairSlotIndex:
		i: int = HashMap.hash(key) % len(self.rows)
		s: Slot = self.rows[i]
		while s != None:
			if s.key == key:
				return PairSlotIndex(s, i)
			s = s.next_
		return PairSlotIndex(None, i)

	def exists(self, key: str) -> bool:
		return True if self.find(key).slot != None else False

	def get(self, key: str) -> str:
		p: PairSlotIndex = self.find(key)
		if p.slot == None:
			return None
		return p.slot.get()

	def set(self, key: str, value: str) -> int:
		if self.size > self.max_size:
			self.evict()

		p: PairSlotIndex = self.find(key)
		if p.slot != None:
			self.size += len(value) - len(p.slot.value)
			p.slot.set(value)
			return 1

		self.size += len(value)
		s: Slot = Slot(key, value, self.rows[p.index])
		self.rows[p.index] = s
		return 0

	class DelPair:
		def __init__(self) -> None:
			self.keys: int = 0
			self.size: int = 0

	def delete(self, key: str) -> "HashMap.DelPair":
		ret: "HashMap.DelPair" = HashMap.DelPair()
		i: int = HashMap.hash(key) % len(self.rows)
		prev: Slot = None
		s: Slot = self.rows[i]
		while s != None:
			if s.key == key:
				if prev == None:
					self.rows[i] = s.next_
				else:
					prev.next_ = s.next_
				ret.keys += 1
				ret.size = len(s.value)
				self.size -= ret.size
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
			s: Slot = self.rows[row]
			while s != None and i < HashMap.CANDIDATE_COUNT:
				if oldest == 0 or oldest > s.timestamp:
					key = s.key
					oldest = s.timestamp
				i += 1
				s = s.next_
		return key

	def evict(self) -> int:
		size_freed: int = 0
		while self.size > self.max_size:
			key: str = self.sample()
			size_freed += self.delete(key).size
		return size_freed
