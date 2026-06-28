# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mjlib is a C++20 robotics library by mjbots, providing foundational utilities, async I/O, a multiplex communication protocol, telemetry/data recording, and microcontroller abstractions targeting STM32G4. Licensed under Apache 2.0.

## Build System

Bazel is the build system. A vendored bazel binary is at `./tools/bazel`.

### Common Commands

```bash
# Run all host tests (C++ and Python)
./tools/bazel test --config=host //:host

# Run tests for a single module
./tools/bazel test --config=host //mjlib/base:test
./tools/bazel test --config=host //mjlib/io:test
./tools/bazel test --config=host //mjlib/multiplex:test
./tools/bazel test --config=host //mjlib/telemetry:test

# Build for STM32G4 target
./tools/bazel build --config=target //:target
```

The `--config=host` flag is required for host builds (adds `-lrt` and `-Werror`). The `--config=target` flag cross-compiles for STM32G4.

### Build Configuration

- C++20 with LLVM toolchain via `com_github_mjbots_bazel_toolchain`
- `-Werror` is enabled for both host and target builds
- Test output is configured to show only errors (`--test_output=errors`)
- Each module has a single `cc_test` target named `test` that bundles all test files

## Architecture

### Module Layout

All code lives under `mjlib/` with these modules:

- **`base/`** - Foundation: error handling, streams, serialization archives, data structures, algorithms (PID, CRC, windowed average)
- **`io/`** - Async I/O built on Boost.Asio: stream abstractions, stream factory (serial/TCP/stdio), timers, realtime executor
- **`micro/`** - Embedded/microcontroller layer: static allocation (pool_ptr, static_vector), async primitives without std::future, command manager, persistent config over flash
- **`multiplex/`** - Communication protocol for embedded networks: frame-based protocol over RS-485/SocketCAN/FDCAN-USB, register-based RPC, client/server implementations. Python bindings included.
- **`telemetry/`** - Binary data recording and playback with snappy compression, schema system, JSON export. Python reader included.
- **`imgui/`** - ImGui integration for visualization

### Key Architectural Patterns

**Visitor-based serialization** (`base/visitor.h`): The central abstraction. Structs implement a templated `Serialize(Archive*)` method that calls `archive->Visit(mjlib::base::MakeNameValuePair(&field, "name"))` for each field. Archives (JSON5, binary, program_options, clipp, INI) then process all fields generically. This is used pervasively for configuration, telemetry, and protocol encoding.

**Dual async models**: `mjlib/io` uses Boost.Asio executors with `fu2::unique_function` callbacks for host platforms. `mjlib/micro` provides a parallel async framework using fixed-size `InplaceFunction` callbacks suitable for embedded targets with no heap allocation.

**Transport abstraction in multiplex**: The multiplex protocol is transport-agnostic. `FrameStream` is the abstract interface, with concrete implementations for RS-485 serial, Linux SocketCAN, and FDCAN-USB. Clients use `StreamAsioClientBuilder` to construct the appropriate transport from command-line options.

**Static allocation for embedded**: The `micro/` module avoids dynamic allocation entirely. `PoolPtr`, `PoolMap`, `PoolArray`, and `StaticVector` provide containers with compile-time-bounded storage. This pattern extends to the async framework where callback sizes are fixed at compile time.
