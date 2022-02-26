#include <unordered_map>
#include <utility>

#include "tensorflow/core/platform/env.h"

namespace tensorflow {

ClientSession::ClientSession(const Scope& scope, const string& target)
    : ClientSession(scope, Impl::MakeDefaultSessionOptions(target)) {}

ClientSession::ClientSession(const Scope& scope) : ClientSession(scope, "") {}

ClientSession::ClientSession(const Scope& scope,
                             const SessionOptions& session_options) {
  Session* new_session;
  Status status = NewSession(session_options, &new_session);
  TF_CHECK_OK(status) << status;
  impl_.reset(new Impl(new_session, scope.graph_as_shared_ptr()));
  CHECK_NOTNULL(impl()->session_.get());
}

// Define destructor here so we can forward declare `Impl` in client_session.h.
// If we define a dtor in the header file or use the default dtor,
ClientSession::~ClientSession() {}

SessionOptions ClientSession::Impl::MakeDefaultSessionOptions(
    const string& target) {
  SessionOptions options;
  options.env = Env::Default();
  options.target = target;
  return options;
}

Status ClientSession::Impl::MaybeExtendGraph() const {
  mutex_lock l(mu_);
  int num_nodes = graph_->num_node_ids();
  if (num_nodes > last_num_graph_nodes_) {
    GraphDef graph_def;
    graph_->ToGraphDefSubRange(&graph_def, last_num_graph_nodes_);
    last_num_graph_nodes_ = num_nodes;
    return session_->Extend(graph_def);
  }
  return Status::OK();
}
