#include "micro_hashmap.h"
#include <time.h>

char heap[1024 * 1024 * 1024];
size_t heap_pos = 0;

unsigned long now() {
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1000 * 1000 * 1000 + t.tv_nsec ;
}

HashMap::Slot::Slot(std::string& key, std::string& value, UniquePtr<Slot> next) : key(std::move(key)), value(std::move(value)), next(std::move(next)) {
	//this->timestamp = now();
}

void HashMap::Slot::set(std::string& value) {
	this->value = std::move(value);
	//this->timestamp = now();
}

std::string const& HashMap::Slot::get() {
	this->timestamp = now();
	return this->value;
}

void HashMap::EvictionPool::populate() {
	Slot* candidates[HashMap::EvictionPool::CANDIDATE_COUNT];
	for (int i = 0; i < HashMap::EvictionPool::CANDIDATE_COUNT;) {
		int row = ((std::rand() % this->hashmap.length) + this->hashmap.length) % this->hashmap.length;
		std::shared_lock lock(this->hashmap.rows[row].lock);
		for (Slot* s = this->hashmap.rows[row].head.get();
				s != nullptr && i < HashMap::EvictionPool::CANDIDATE_COUNT; s = s->next.get()) {
			candidates[i] = s;
			i++;
		}
	}

	// insert the candidates
	for (int i = 0; i < HashMap::EvictionPool::CANDIDATE_COUNT; i++) {
		Slot* candidate = candidates[i];
		for (int j = 0; j < HashMap::EvictionPool::MAX_LENGTH; j++) {
			if (this->pool[j] == nullptr) {
				this->pool[j] = MAKE_UNIQUE<EvictionPoolEntry>(*candidate);
				break;
			} else if (this->pool[j]->timestamp < candidate->timestamp) {
				for (int k = HashMap::EvictionPool::MAX_LENGTH - 1; k > j; k--) {
					this->pool[k] = std::move(this->pool[k - 1]);
				}
				this->pool[j]= MAKE_UNIQUE<EvictionPoolEntry>(*candidate);
				break;
			}
		}
	}
}

std::optional<std::reference_wrapper<std::string const>> HashMap::EvictionPool::pop() {
	std::optional<std::reference_wrapper<std::string const>> ret;
	if (this->pool[0] != nullptr) {
		ret = std::reference_wrapper<std::string const>(this->pool[0]->key);
		for (int i = 0; i < HashMap::EvictionPool::MAX_LENGTH - 1; i++) {
			this->pool[i] = std::move(this->pool[i + 1]);
		}
		this->pool[HashMap::EvictionPool::MAX_LENGTH - 1] = nullptr;
	}
	return ret;
}

long HashMap::hash(std::string const& key) {
	long h = 0;
	for (size_t i = 0; i < key.length(); i++) {
		h = (h * 31) + key[i];
	}
	return h;
}

static int row_i = 0;
int HashMap::get_row(std::string const& key) {
	(void) key;
	//return ((int) (HashMap::hash(key) % this->length) + this->length) % this->length;
	return (row_i++ % this->length);
	//return row_i++ / 2048;
}

volatile int something = 0;
// must call holding a lock on the row
HashMap::Slot* HashMap::find(std::string const& key, int row) {
	//(void) key;
	for (Slot* s = this->rows[row].head.get(); s != nullptr; s = s->next.get()) {
		/*
		if (s->key == key) {
			return s;
		}
		*/
		//something++;
		if (&s->key == &key) {
			return s;
		}
	}
	return nullptr;
}

bool HashMap::exists(std::string const& key) {
	std::shared_lock map_lock(this->lock);
	int i = HashMap::get_row(key);
	std::shared_lock row_lock(this->rows[i].lock);
	Slot *s = this->find(key, i);
	return (s != nullptr);
}

std::optional<std::reference_wrapper<std::string const>> HashMap::get(std::string const& key) {
	std::shared_lock map_lock(this->lock);
	int i = this->get_row(key);
	std::shared_lock row_lock(this->rows[i].lock);
	Slot *s = this->find(key, i);
	if (s == nullptr) {
		return std::nullopt;
	}
	return std::reference_wrapper<std::string const>(s->get());
}

int HashMap::set(std::string& key, std::string& value) {
	/*
	std::shared_lock map_lock(this->lock);
	if (this->size > this->max_size) {
		this->evict();
	}
	*/
	int i = HashMap::get_row(key);
	//std::unique_lock row_lock(this->rows[i].lock);
	Slot *s = this->find(key, i);
	if (s != nullptr) {
		//this->size += value.length() - s->value.length();
		s->set(value);
		return 1;
	}
	//this->size += value.length();
	UniquePtr<Slot> s2 = MAKE_UNIQUE<Slot>(key, value, std::move(this->rows[i].head));
	this->rows[i].head = std::move(s2);
	return 0;
}

std::pair<int, int> HashMap::del(std::string const& key) {
	std::pair<int, int> ret(0, 0);
	Slot* prev = nullptr;
	std::shared_lock map_lock(this->lock);
	int i = HashMap::get_row(key);
	std::unique_lock row_lock(this->rows[i].lock);
	for (Slot* s = this->rows[i].head.get(); s != nullptr; s = s->next.get()) {
		if (s->key == key) {
			UniquePtr<Slot> next = std::move(s->next);
			if (prev == nullptr) {
				this->rows[i].head = std::move(next);
			} else {
				prev->next = std::move(next);
			}
			ret.first++;
			ret.second = s->value.length();
			this->size -= ret.second;
			break;
		}
		prev = s;
	}
	return ret;
}

// must have read lock on map
int HashMap::evict() {
	int size_freed = 0;
	while (this->size > this->max_size) {
		std::string const* best_key = nullptr;
		while (best_key == nullptr) {
			this->eviction_pool.populate();
			std::optional<std::reference_wrapper<std::string const>> candidate_key = this->eviction_pool.pop();
			if (candidate_key.has_value() && this->exists(candidate_key->get())) {
				best_key = &(candidate_key->get());
			}
			size_freed += this->del(*best_key).second;
		}
	}
	return size_freed;
}

int main() {
	HashMap map(24 * 1024 * 1024, 1024);
	for (int i = 0; i < 2 * 1000 * 1000; i++) {
		std::string k = std::to_string(i);
		std::string v = "xxx";
		map.set(k, v);
	}
	return 0;
}
