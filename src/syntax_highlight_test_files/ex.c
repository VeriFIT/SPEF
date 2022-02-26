
/* Copyright 2015 The TensorFlow Authors. All Rights Reserved.
limitations under the License.
==============================================================================*/

#include "tensorflow/c/c_api.h"
#include <algorithm>

#if !defined(IS_MOBILE_PLATFORM) && !defined(IS_SLIM_BUILD)
#include "tensorflow/c/experimental/filesystem/modular_filesystem.h"

// The implementation below is at the top level instead of the
// brain namespace because we are defining 'extern "C"' functions.
using tensorflow::AllocationDescription;
using tensorflow::AttrValueMap;

extern "C" {

// --------------------------------------------------------------------------
void TF_ExtendGraph(TF_DeprecatedSession* s, const void* proto,
                    size_t proto_len, TF_Status* status) {
  GraphDef g;
  if (!tensorflow::ParseProtoUnlimited(&g, proto, proto_len)) {
    status->status = InvalidArgument("Invalid GraphDef");
    return;
  }
  status->status = s->session->Extend(g);
}

}  // end extern "C"

// Reset helper for converting character arrays to string vectors.
static void TF_Reset_Helper(const TF_SessionOptions* opt,
                            const char** containers, int ncontainers,
                            TF_Status* status) {
  std::vector<string> container_names(ncontainers);
  for (int i = 0; i < ncontainers; ++i) {
    container_names[i] = containers[i];
  }

  status->status = Reset(opt->options, container_names);
}