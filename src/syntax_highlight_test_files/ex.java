package org.tensorflow;
import java.util.Iterator;

/**
 * A data flow graph representing a TensorFlow computation.
 * the {@link #close()} method then the Graph object is no longer needed.
 */
public final class Graph implements ExecutionEnvironment, AutoCloseable {
  public Graph() {
    nativeHandle = allocate();
  }
  Graph(long nativeHandle) {
    this.nativeHandle = nativeHandle;
  }

  /**
   * Release resources associated with the Graph.
   * is not usable after close returns.
   */
  @Override
  public void close() {
    synchronized (nativeHandleLock) {
      if (nativeHandle == 0) {
        return;
      }
      while (refcount > 0) {
        try {
          nativeHandleLock.wait();
        } catch (InterruptedException e) {
          Thread.currentThread().interrupt();
          // Possible leak of the graph in this case?
          return;
        }
      }
      delete(nativeHandle);
      nativeHandle = 0;
    }
  }
