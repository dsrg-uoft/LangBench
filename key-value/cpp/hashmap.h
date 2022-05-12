#ifndef HASHMAP_H
#define HASHMAP_H

#include <mutex>
#include <memory>
#include <shared_mutex>
#include <atomic>
#include <string>
#include <string_view>
#include <optional>
#include <functional>
#include <utility>
#include <cstring>

template <typename T> class DummyPtr {
public:
	DummyPtr() : DummyPtr(nullptr) {
		return;
	}
	DummyPtr(T* p) : ptr(p) {
		return;
	}
	T* get() {
		return this->ptr;
	}
	T* operator->() {
		return this->ptr;
	}
	friend bool operator==(DummyPtr const& a, std::nullptr_t b) {
		return a.ptr == b;
	}
	friend bool operator!=(DummyPtr const& a, std::nullptr_t b) {
		return a.ptr != b;
	}
private:
	T* ptr;
};

/*
template <typename T> using UniquePtr = DummyPtr<T>;
#define MAKE_UNIQUE make_dummy
*/

template <typename T> using UniquePtr = std::unique_ptr<T>;
#define MAKE_UNIQUE std::make_unique

extern char heap[];
extern size_t heap_pos;

template <typename T, typename... Args> static inline UniquePtr<T> make_dummy(Args&&... args) {
	void* p = heap + heap_pos;
	heap_pos += sizeof(T);
	return DummyPtr(new (p) T(std::forward<Args>(args)...));
}

class HashMap {
private:
	class Slot {
	public:
		std::string const key;
		std::string value;
		unsigned long timestamp;
		UniquePtr<Slot> next;

		Slot(std::string& key, std::string& value, UniquePtr<Slot> next);
		void set(std::string& value);
		std::string const& get();
	};

	class Row {
	public:
		UniquePtr<Slot> head;
		std::shared_mutex lock;

		Row() : head(nullptr) {
			return;
		}
	};

	class EvictionPool {
	private:
		class EvictionPoolEntry {
		public:
			std::string const key;
			unsigned long const timestamp;

			EvictionPoolEntry(Slot const& s) : key(s.key), timestamp(s.timestamp) {
				return;
			}
		};

		static int const MAX_LENGTH = 16;
		static int const CANDIDATE_COUNT = 5;
		UniquePtr<EvictionPoolEntry> pool[MAX_LENGTH];
		HashMap &hashmap;

	public:
		EvictionPool(HashMap &hm) : hashmap(hm) {
			return;
		}
		void populate();
		std::optional<std::string> pop();
	};

	unsigned long const max_size;

	// need to hold read lock to use rows,
	// write lock to change row size (grow/shrink map)
	// atomic int for stored size avoids needing write lock
	std::unique_ptr<Row[]> rows;
	int length;
	std::atomic<unsigned long> size;

	static long hash(std::string const& key);
	int get_row(std::string const& key);
	Slot* find(std::string const& key, int row);
	bool exists(std::string const& key);
	std::pair<int, int> del(std::string  const& key);
	std::string sample();
	int evict();
	static int const CANDIDATE_COUNT = 5;
public:
	HashMap(unsigned long max_size, int num_rows) : max_size(max_size) {
		this->length = num_rows;
		this->rows = std::make_unique<Row[]>(this->length);
		this->size = 0;
	}
	std::optional<std::string> get(std::string const& key);
	int set(std::string& key, std::string& value);
};

#endif // HASHMAP_H
