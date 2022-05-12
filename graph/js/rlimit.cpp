#include <sys/resource.h>
#include <node.h>

namespace rlimit_set_stack {
	using v8::FunctionCallbackInfo;
	using v8::Local;
	using v8::Object;
	using v8::Value;

	void set_rlimit_stack(FunctionCallbackInfo<Value> const& args) {
		(void) args;
		struct rlimit rlim;
		getrlimit(RLIMIT_STACK, &rlim);
		//printf("soft: %lu hard: %lu\n", rlim.rlim_cur, rlim.rlim_max);
		rlim.rlim_cur = 128 * 1024 * 1024;
		rlim.rlim_max = 128 * 1024 * 1024;
		setrlimit(RLIMIT_STACK, &rlim);
	}

	void Initialize(Local<Object> exports) {
		NODE_SET_METHOD(exports, "rlimit_set_stack", set_rlimit_stack);
	}

	NODE_MODULE(NODE_GYP_MODULE_NAME, Initialize)
}
