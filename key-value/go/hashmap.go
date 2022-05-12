package main

import "sync"
import "sync/atomic"
import "math/rand"
import "time"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

type Row struct {
	head *Slot
	lock sync.RWMutex
}

type Slot struct {
	key string
	value string
	timestamp int64
	next *Slot
}

func newSlot(key string, value string, next *Slot) *Slot {
	var s *Slot = new(Slot)
	s.key = key
	s.value = value
	s.next = next
	s.timestamp = time.Now().UnixNano()
	return s
}

func (this *Slot) set(value string) {
	this.value = value
	this.timestamp = time.Now().UnixNano()
}

func (this *Slot) get() *string {
	this.timestamp = time.Now().UnixNano()
	return &this.value
}

type EvictionPoolEntry struct {
	key string
	timestamp int64
}

func newEvictionPoolEntry(s *Slot) *EvictionPoolEntry {
	var epe *EvictionPoolEntry = new(EvictionPoolEntry)
	epe.key = s.key
	epe.timestamp = s.timestamp
	return epe
}

const MAX_LENGTH int = 16
const CANDIDATE_COUNT int = 5
type EvictionPool struct {
	pool []*EvictionPoolEntry
	hashmap *HashMap
}

type HashMap struct {
	max_size int64
	rows []Row
	length int
	size int64 // atomic
}

func NewHashMap(max_size int64, num_rows int) *HashMap {
	var hm *HashMap = new(HashMap)
	hm.max_size = max_size
	hm.length = num_rows
	hm.rows = make([]Row, hm.length)
	return hm
}

func hash(key string) int64 {
	var h int64 = 0
	for i := 0; i < len(key); i++ {
		h = (h * 31) + int64(key[i])
	}
	return h
}

func (this *HashMap) get_row(key string) int {
	return (int(hash(key) % int64(this.length)) + this.length) % this.length
}

func (this *HashMap) find(key string, row int) *Slot {
	for s := this.rows[row].head; s != nil; s = s.next {
		if s.key == key {
			return s
		}
	}
	return nil
}

func (this *HashMap) exists(key string) bool {
	var i int = this.get_row(key)
	this.rows[i].lock.RLock()
	defer this.rows[i].lock.RUnlock()
	var s *Slot = this.find(key, i)
	return (s != nil)
}

type DelPair struct {
	count int
	bytes int
}

func (this *HashMap) del(key string) DelPair {
	var ret DelPair = DelPair { 0, 0 }
	var prev *Slot = nil
	var i int = this.get_row(key)
	this.rows[i].lock.Lock()
	defer this.rows[i].lock.Unlock()

	for s := this.rows[i].head; s != nil; s = s.next {
		if s.key == key {
			if prev == nil {
				this.rows[i].head = s.next
			} else {
				prev.next = s.next
			}
			ret.count++;
			ret.bytes = len(s.value)
			atomic.AddInt64(&this.size, int64(-ret.bytes))
			break
		}
		prev = s
	}
	return ret
}

func (this *EvictionPool) populate() {
	var candidates []*Slot = make([]*Slot, CANDIDATE_COUNT)
	for i := 0; i < CANDIDATE_COUNT; {
		var row int = ((rand.Int() % this.hashmap.length) + this.hashmap.length) % this.hashmap.length
		{
			this.hashmap.rows[row].lock.RLock()
			for s := this.hashmap.rows[row].head; s != nil && i < CANDIDATE_COUNT; s = s.next {
				candidates[i] = s
				i++
			}
			this.hashmap.rows[row].lock.RUnlock()
		}
	}

	// insert the candidates
	for i := 0; i < CANDIDATE_COUNT; i++ {
		var candidate *Slot = candidates[i]
		for j := 0; j < MAX_LENGTH; j++ {
			if this.pool[j] == nil {
				this.pool[j] = newEvictionPoolEntry(candidate)
				break
			} else if this.pool[j].timestamp < candidate.timestamp {
				for k := MAX_LENGTH - 1; k > j; k-- {
					this.pool[k] = this.pool[k - 1]
				}
				this.pool[j] = newEvictionPoolEntry(candidate)
				break
			}
		}
	}
}

func (this *EvictionPool) pop() *string {
	var ret *string = nil
	if this.pool[0] != nil {
		ret = &this.pool[0].key
		for i := 0; i < MAX_LENGTH - 1; i++ {
			this.pool[i] = this.pool[i + 1]
		}
		this.pool[MAX_LENGTH - 1] = nil
	}
	return ret
}

func (this *HashMap) sample() string {
	var key string
	var oldest int64 = 0
	for i := 0; i < CANDIDATE_COUNT; {
		var row int = ((rand.Int() % this.length) + this.length) % this.length
		{
			this.rows[row].lock.RLock()
			for s := this.rows[row].head; s != nil && i < CANDIDATE_COUNT; s = s.next {
				if oldest == 0 || oldest > s.timestamp {
					key = s.key
					oldest = s.timestamp
				}
			}
			i++;
			this.rows[row].lock.RUnlock()
		}
	}
	return key
}

func (this *HashMap) evict() int {
	var size_freed int = 0
	for atomic.LoadInt64(&this.size) > this.max_size {
		var key string = this.sample()
		size_freed += this.del(key).bytes
	}
	return size_freed
}

func (this *HashMap) Get(key string) *string {
	var i int = this.get_row(key)
	this.rows[i].lock.RLock()
	defer this.rows[i].lock.RUnlock()
	var s *Slot = this.find(key, i)
	if s == nil {
		return nil
	}
	return s.get()
}

func (this *HashMap) Set(key string, value string) int {
	if atomic.LoadInt64(&this.size) > this.max_size {
		this.evict();
	}
	var i int = this.get_row(key)
	this.rows[i].lock.Lock()
	defer this.rows[i].lock.Unlock()
	var s *Slot = this.find(key, i)
	if s != nil {
		atomic.AddInt64(&this.size, int64(len(value) - len(s.value)))
		s.set(value)
		return 1
	}
	atomic.AddInt64(&this.size, int64(len(value)))
	s = newSlot(key, value, this.rows[i].head)
	this.rows[i].head = s
	return 0
}
