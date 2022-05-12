

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.concurrent.atomic.AtomicLong;
import java.util.Random;

class HashMap {
	private static class Row {
		public Slot head;
		public ReadWriteLock lock;

		public Row() {
			this.lock = new ReentrantReadWriteLock();
		}
	}

	private static class Slot {
		public String key;
		public String value;
		public long timestamp;
		public Slot next;

		public Slot(String key, String value, Slot next) {
			this.key = key;
			this.value = value;
			this.timestamp = System.nanoTime();
			this.next = next;
		}

		public void set(String value) {
			this.value = value;
			this.timestamp = System.nanoTime();
		}

		public String get() {
			this.timestamp = System.nanoTime();
			return this.value;
		}
	}

	private class EvictionPool {
		private class EvictionPoolEntry {
			private String key;
			private long timestamp;

			public EvictionPoolEntry(Slot s) {
				this.key = s.key;
				this.timestamp = s.timestamp;
			}
		}

		private EvictionPoolEntry[] pool;
		private Random rand;
		private static final int MAX_LENGTH = 16;
		private static final int CANDIDATE_COUNT = 5;

		public EvictionPool() {
			this.pool = new EvictionPoolEntry[HashMap.EvictionPool.MAX_LENGTH];
			this.rand = new Random();
		}

		public synchronized void populate() {
			Slot[] candidates = new Slot[HashMap.EvictionPool.CANDIDATE_COUNT];
			for (int i = 0; i < candidates.length;) {
				int row = ((this.rand.nextInt() % HashMap.this.rows.length) + HashMap.this.rows.length) % HashMap.this.rows.length;
				Lock row_lock = HashMap.this.rows[row].lock.readLock();
				row_lock.lock();
				try {
					for (Slot s = HashMap.this.rows[row].head;
							s != null && i < candidates.length; s = s.next) {
						candidates[i] = s;
						i++;
					}
				} finally {
					row_lock.unlock();
				}
			}

			// insert the candidates
			for (int i = 0; i < candidates.length; i++) {
				Slot candidate = candidates[i];
				for (int j = 0; j < this.pool.length; j++) {
					if (this.pool[j] == null) {
						this.pool[j] = new EvictionPoolEntry(candidate);
						break;
					} else if (this.pool[j].timestamp < candidate.timestamp) {
						for (int k = this.pool.length - 1; k > j; k--) {
							this.pool[k] = this.pool[k - 1];
						}
						this.pool[j] = new EvictionPoolEntry(candidate);
						break;
					}
				}
			}
		}

		public synchronized String pop() {
			String k = null;
			if (this.pool[0] != null) {
				k = this.pool[0].key;
				for (int i = 0; i < this.pool.length - 1; i++) {
					this.pool[i] = this.pool[i + 1];
				}
				this.pool[this.pool.length - 1] = null;
			}
			return k;
		}
	}

	private final long max_size;

	// need to hold read lock to use rows, write lock to change row size (grow/shrink map)
	// atomic int for stored size avoids needing write lock
	private Row[] rows;
	private AtomicLong size;
	private EvictionPool eviction_pool;
	private Random rand;
	private static final int CANDIDATE_COUNT = 5;

	public HashMap(long max_size, int num_rows) {
		this.rows = new Row[num_rows];
		for (int i = 0; i < this.rows.length; i++) {
			this.rows[i] = new Row();
		}
		this.size = new AtomicLong();
		this.rand = new Random();
		this.max_size = max_size;
	}

	private static long hash(String s) {
		long h = 0;
		for (int i = 0; i < s.length(); i++) {
			h = (h * 31) + s.charAt(i);
		}
		return h;
	}

	public static int row_i = 0;
	private int get_row(String s) {
		return ((int) (HashMap.hash(s) % this.rows.length) + this.rows.length) % this.rows.length;
		//return (row_i++ % this.rows.length);
		//return row_i++ / 2048;
	}

	public static volatile int something = 0;
	// returns holding row lock
	private Slot find(String key, int row) {
		for (Slot s = this.rows[row].head; s != null; s = s.next) {
			if (s.key.equals(key)) {
				return s;
			}
			/*
			if (s.key == key) {
				return s;
			}
			*/
		}
		return null;
	}

	private boolean exists(String key) {
		Slot s = null;
		int i = this.get_row(key);
		Lock row_lock = this.rows[i].lock.readLock();
		row_lock.lock();
		try {
			s = this.find(key, i);
		} finally {
			row_lock.unlock();
		}
		return (s != null);
	}

	public String get(String key) {
		int i = this.get_row(key);
		Lock row_lock = this.rows[i].lock.readLock();
		row_lock.lock();
		try {
			Slot s = this.find(key, i);
			if (s == null) {
				return null;
			}
			return s.get();
		} finally {
			row_lock.unlock();
		}
	}

	public int set(String key, String val) {
		// need to do eviction first / seperately
		// we cannot evict while holding a write lock on the row as you could have
		// two threads in eviction while both holding row write locks -> deadlock
		// we'll always be a bit behind on reducing the size, but meh
		// this is similar to redis as they check before executing any command
		if (this.size.get() > this.max_size) {
			this.evict();
		}

		int i = this.get_row(key);
		Lock row_lock = this.rows[i].lock.writeLock();
		row_lock.lock();
		try {
			Slot s = this.find(key, i);
			if (s != null) {
				this.size.addAndGet(val.length() - s.value.length());
				s.set(val);
				return 1;
			}
			this.size.addAndGet(val.length());
			s = new Slot(key, val, this.rows[i].head);
			this.rows[i].head = s;
			return 0;
		} finally {
			row_lock.unlock();
		}
	}

	public static class DelPair {
		public int keys;
		public int size;
	}

	public DelPair del(String key) {
		DelPair ret = new DelPair();
		int i = this.get_row(key);
		Slot prev = null;
		Lock row_lock = this.rows[i].lock.writeLock();
		row_lock.lock();
		try {
			for (Slot s = this.rows[i].head; s != null; s = s.next) {
				if (s.key.equals(key)) {
					if (prev == null) {
						this.rows[i].head = s.next;
					} else {
						prev.next = s.next;
					}
					ret.keys++;
					ret.size = s.value.length();
					this.size.addAndGet(-ret.size);
					break;
				}
				prev = s;
			}
		} finally {
			row_lock.unlock();
		}
		return ret;
	}

	private String sample() {
		String key = null;
		long oldest = 0;
		for (int i = 0; i < CANDIDATE_COUNT;) {
			int row = ((this.rand.nextInt() % HashMap.this.rows.length) + HashMap.this.rows.length) % HashMap.this.rows.length;
			Lock row_lock = HashMap.this.rows[row].lock.readLock();
			row_lock.lock();
			try {
				for (Slot s = HashMap.this.rows[row].head;
						s != null && i < CANDIDATE_COUNT; s = s.next) {
					if (oldest == 0 || oldest > s.timestamp) {
						key = s.key;
						oldest = s.timestamp;
					}
					i++;
				}
			} finally {
				row_lock.unlock();
			}
		}
		return key;
	}

	private int evict() {
		int size_freed = 0;
		while (this.size.get() > this.max_size) {
			String key = this.sample();
			size_freed += this.del(key).size;
		}
		return size_freed;
	}

	public void dump() {
		for (int i = 0; i < this.rows.length; i++) {
			for (Slot s = this.rows[i].head; s != null; s = s.next) {
				System.out.print(i + " " + s + " " + s.key + " " + s.value + "\n");
			}
		}
		/*
		try {
		java.lang.reflect.Field f = sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
		f.setAccessible(true);
		sun.misc.Unsafe unsafe = (sun.misc.Unsafe) f.get(null);
		Runtime r = Runtime.getRuntime();
		Object[] o = new Object[1];
		for (int row = 0; row < this.rows.length; row++) {
			int i = 0;
			long last = 0;
			for (Slot s = this.rows[row].head; s != null; s = s.next) {
				o[0] = s;
				//long x = unsafe.getInt(o, unsafe.arrayBaseOffset(Object[].class));
				long x = r.addressOfObject(s);
				if (i > 0) {
					System.out.print("diff: " + (x - last)  + "\n");
				}
				last = x;
				i++;
			}
		}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
		*/
	}
}
