import Foundation
import TensorFlowLiteC

#if os(Linux)
  import SwiftGlibc
#else
  import Darwin
#endif

/// A TensorFlow Lite interpreter that performs inference from a given model.
public final class Interpreter {
  /// The configuration options for the `Interpreter`.
  public let options: Options?

@available(*, deprecated, renamed: "Interpreter.Options")
public typealias InterpreterOptions = Interpreter.Options

extension String {
  /*
  asdf
  asdf
  */
  init?(cFormat: UnsafePointer<CChar>, arguments: CVaListPointer) {
    #if os(Linux)
      let length = Int(vsnprintf(nil, 0, cFormat, arguments) + 1) // null terminator
      guard length > 0 else { return nil }
      let buffer = UnsafeMutablePointer<CChar>.allocate(capacity: length)
      defer {
        buffer.deallocate()
      }
      guard vsnprintf(buffer, length, cFormat, arguments) == length - 1 else { return nil }
      self.init(validatingUTF8: buffer)
    #else
      var buffer: UnsafeMutablePointer<CChar>?
      guard vasprintf(&buffer, cFormat, arguments) != 0, let cString = buffer else { return nil }
      self.init(validatingUTF8: cString)
    #endif
  }
}