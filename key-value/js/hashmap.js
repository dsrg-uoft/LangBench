

function now() {
	let t = process.hrtime();
	return (t[0] * 1000 * 1000 * 1000) + t[1];
}

class Slot {
	constructor(key, value, next) {
		this.timestamp = now();
		this.next = next;
		this.key = key;
		this.value_ = value;
	}

	get value() {
		this.timestamp = now();
		return this.value_;
	}

	set value(value) {
		this.value_ = value;
		this.timestamp = now();
	}
}

const EVICTIONPOOL_MAX_LENGTH = 16;
const EVICTIONPOOL_CANDIDATE_COUNT = 5;
class EvictionPool {
	constructor(hashmap) {
		this.hashmap = hashmap;
		this.pool = new Array(EVICTIONPOOL_MAX_LENGTH);
	}

	populate() {
		let candidates = [];
		while (candidates.length < EVICTIONPOOL_CANDIDATE_COUNT) {
			let row = Math.floor(Math.random() * this.hashmap.rows.length);
			for (let s = this.hashmap.rows[row];
				s != null && candidates.length < EVICTIONPOOL_CANDIDATE_COUNT;
				s = s.next) {
				candidates.push(s);
			}
		}

		for (let i = 0; i < candidates.length; i++) {
			let candidate = candidates[i];

			for (let j = 0; j < this.pool.length; j++) {
				if (this.pool[j] == null) {
					this.pool[j] = {
						key: candidate.key,
						timestamp: candidate.timestamp,
					};
					break;
				} else if (this.pool[j].timestamp < candidate.timestamp) {
					for (let k = this.pool.length - 1; k > j; k--) {
						this.pool[k] = this.pool[k - 1];
					}
					this.pool[j] = {
						key: candidate.key,
						timestamp: candidate.timestamp,
					};
					break;
				}
			}
		}
	}

	pop() {
		let k = null;
		if (this.pool[0] != null) {
			k = this.pool[0].key;
			for (let i = 0; i < this.pool.length - 1; i++) {
				this.pool[i] = this.pool[i + 1];
			}
			this.pool[this.pool.length - 1] = null;
		}
		return k;
	}
}

class HashMap {
	constructor(max_size, num_rows) {
		this.rows = new Array(num_rows);
		for (let i = 0; i < this.rows.length; i++) {
			this.rows[i] = null;
		}
		this.size = 0;
		this.max_size = max_size;
	}

	static hash(s) {
		let h = 0;
		for (let i = 0; i < s.length; i++) {
			h = ((h * 31) + s.charCodeAt(i)) & (~0);
		}
		return h;
	}

	find(key) {
		let i = HashMap.hash(key) % this.rows.length;
		for (let s = this.rows[i]; s != null; s = s.next) {
			if (s.key == key) {
				return {
					slot: s,
					index: i,
				};
			}
		}
		return {
			slot: null,
			index: i,
		};
	}

	exists(key) {
		return (this.find(key).slot != null) ? true : false;
	}

	op_get(key) {
		let p = this.find(key);
		if (p.slot == null) {
			return null;
		}
		return p.slot.value;
	}

	op_set(key, val) {
		if (this.size > this.max_size) {
			this.evict();
		}

		let p = this.find(key);
		if (p.slot != null) {
			this.size += val.length - p.slot.value_.length;
			p.slot.value = val;
			return 1;
		}
		this.size += val.length;
		let s = new Slot(key, val, this.rows[p.index]);
		this.rows[p.index] = s;
		return 0;
	}

	del(key) {
		let ret = {
			keys: 0,
			size: 0,
		};
		let i = HashMap.hash(key) % this.rows.length;
		let prev = null;
		for (let s = this.rows[i]; s != null; s = s.next) {
			if (s.key == key) {
				if (prev == null) {
					this.rows[i] = s.next;
				} else {
					prev.next = s.next;
				}
				ret.keys++;
				ret.size = s.value_.length;
				this.size -= ret.size;
				break;
			}
			prev = s;
		}
		return ret;
	}

	sample() {
		let key = null;
		let oldest = 0;
		let i = 0;
		while (i < EVICTIONPOOL_CANDIDATE_COUNT) {
			let row = Math.floor(Math.random() * this.rows.length);
			for (let s = this.rows[row]; s != null && i < EVICTIONPOOL_CANDIDATE_COUNT;
				s = s.next) {
				if (oldest == 0 || oldest > s.timestamp) {
					key = s.key;
					oldest = s.timestamp;
				}
				i++;
			}
		}
		return key;
	}

	evict() {
		let size_freed = 0;
		while (this.size > this.max_size) {
			let key = this.sample();
			size_freed += this.del(key).size;
		}
		return size_freed;
	}
}

module.exports = HashMap
