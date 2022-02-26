/*
Licensed under the Apache License, Version 2.0 (the "License");
limitations under the License.
*/

package tensorflow

// #include <stdlib.h>
import (
	"fmt"
	"runtime"
)

type ContextOptions struct {
	// (https://www.tensorflow.org/code/tensorflow/core/protobuf/config.proto).
	Config []byte
	Async bool
}

// c converts the ContextOptions to the C API's TF_ContextOptions.
// Caller takes ownership of returned object.
func (o *ContextOptions) c() (*C.TFE_ContextOptions, error) {
	opt := C.TFE_NewContextOptions()
	if o == nil {
		return opt, nil
	}

	if sz := len(o.Config); sz > 0 {
		status := newStatus()
		cConfig := C.CBytes(o.Config)
		C.TFE_ContextOptionsSetConfig(opt, cConfig, C.size_t(sz), status.c)
		C.free(cConfig)
		if err := status.Err(); err != nil {
			C.TFE_DeleteContextOptions(opt)
			return nil, fmt.Errorf("invalid ContextOptions.Config: %v", err)
		}
	}

	var async uint8
	if o.Async {
		async = 1
	}
	C.TFE_ContextOptionsSetAsync(opt, C.uchar(async))

	return opt, nil
}