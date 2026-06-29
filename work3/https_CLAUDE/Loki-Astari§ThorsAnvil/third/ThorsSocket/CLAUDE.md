# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

ThorsSocket uses a custom autotools-based build system (ThorMaker). It is part of the ThorsAnvil monorepo and expects `THORSANVIL_ROOT` to point to the monorepo root (defaults to `../../`).

```bash
# Build (from repo root or src/ThorsSocket/)
make

# Run all tests
make test

# Run a specific test class
make test-ConnectionSocketTest.*

# Run a specific test method
make test-ConnectionSocketTest.MethodName

# Run test without rebuilding
make testrun.ConnectionSocketTest.*

# Debug a test
make debugrun.ConnectionSocketTest.*

# Clean
make clean
make veryclean    # deep clean including generated files
```

Dependencies: OpenSSL (crypto), ThorsLogging, ThorsSerialize (optional), ZLIB (optional). Tests use GoogleTest. Coverage minimum: 70%.

## Architecture

ThorsSocket provides async I/O over files, pipes, TCP sockets, and SSL/TLS sockets, exposed as `std::iostream`.

### Public API (3 classes)

- **`Socket`** — Client socket for reading/writing. Non-copyable, move-only. Supports yield callbacks for async/coroutine integration (`setReadYield`, `setWriteYield`).
- **`Server`** — Listening server that produces `Socket` objects via `accept()`. Also supports yield callbacks.
- **`SocketStream`** — Template wrapping `Socket` as `std::iostream` with 4KB input/output buffering via `SocketStreamBuffer`.

### Connection Hierarchy (internal polymorphic dispatch)

Socket/Server delegate to a polymorphic `ConnectionBase` hierarchy:

```
ConnectionBase
├── ConnectionClient
│   ├── FileDescriptor
│   │   ├── SimpleFile      (file I/O)
│   │   ├── Pipe            (pipe I/O)
│   │   └── SocketClient    (TCP)
│   │       └── SSocketClient (SSL/TLS)
│   └── SocketClient        (Windows variant)
└── ConnectionServer
    ├── SocketServer         (TCP listen)
    └── SSocketServer        (SSL/TLS listen)
```

Internal `Connection*.h` headers are excluded from installation via `EXCLUDE_HEADERS` in the Makefile.

### Variant-based Construction

Socket/Server are constructed via `std::variant` types (`SocketInit`/`ServerInit`) containing info structs: `FileInfo`, `PipeInfo`, `SocketInfo`, `SSocketInfo`, `ServerInfo`, `SServerInfo`. A visitor pattern (`SocketConnectionBuilder`/`ServerConnectionBuilder`) builds the appropriate Connection subclass.

### Async Integration

Yield callbacks (`YieldFunc`) are the integration point for coroutines/event loops. When I/O would block, the yield function is called. Return `true` to retry the operation, `false` to block until ready. This is how Nisse's coroutine-based server integrates.

### I/O Return Type

All read/write operations return `IOData`:
```cpp
struct IOData {
    std::size_t dataSize;   // bytes transferred
    bool        stillOpen;  // false = connection closed
    bool        blocked;    // true = would block (check yield)
};
```

### SSL/TLS Configuration (SSLctx)

`SSLctx` takes a variadic constructor: `SSLctx(SSLMethodType::Client|Server, args...)` where args can be `ProtocolInfo`, `CipherInfo`, `CertificateInfo`, `CertifcateAuthorityInfo`, `ClientCAListInfo`. Each has an `.apply(SSL_CTX*)` method.

## Source Layout

All library code: `src/ThorsSocket/`
All tests: `src/ThorsSocket/test/`
Test SSL certificates: `src/ThorsSocket/test/data/` (root-ca/, server/, client/)
Test mock infrastructure: `src/ThorsSocket/test/makedependency/`

## Header-Only Source Pattern

Every `.cpp` file guards its content with:
```cpp
#include "ThorsSocketConfig.h"
#ifdef THORS_SOCKET_HEADER_ONLY_INCLUDE
// ... implementation code
#endif
```

Corresponding `.source` files exist and are conditionally included at the bottom of each `.h`:
```cpp
#if THORS_SOCKET_HEADER_ONLY
#include "Socket.source"
#endif
```

When adding new `.cpp` files, follow this pattern to maintain header-only support.

## Error Handling

All errors use `ThorsLogAndThrowDebug` from ThorsLogging:
```cpp
ThorsLogAndThrowDebug("ThorsAnvil::ThorsSocket::ClassName",
    "methodName",
    "descriptive message",
    additionalContext);
```

Always check `Socket::isConnected()` before accessing the socket. The library throws exceptions rather than using error return codes.

## Test Infrastructure

### Mock System

Tests use a generated mock infrastructure in `test/makedependency/`. System calls (read, write, socket, connect, SSL_read, etc.) are wrapped via `MOCK_FUNC()` macros, allowing tests to inject custom behavior without real I/O.

Key files:
- `test/MockHeaderInclude.h` — Function type definitions and `MockAllDefaultFunctions` class with ~50 mocked system calls and sensible defaults
- `test/ConnectionTest.h` — `TestConnection` class for faking `ConnectionClient` behavior in Socket-level tests

Mock usage in tests:
```cpp
// Inject failure on socket()
TA_TestThrow([](){ /* test code */ })
    .expectObjectTA(Socket_NonBlockingGetAddrInfoTwoV1)
    .expectCallTA(socket).inject().toReturn(-1)
    .run();
```

### Integration Tests

Use `ServerStart` helper from `test/SimpleServer.h` for real socket/SSL tests with a background server thread:
```cpp
ServerStart serverHelper;
serverHelper.run(port, serverRequest, [](Socket& socket) {
    // handle connection
});
```

## Namespace

```cpp
namespace ThorsAnvil::ThorsSocket {
    // Public: Socket, Server, SocketStream, SSLctx
    namespace ConnectionType {
        // Internal: SocketClient, SSocketClient, SimpleFile, Pipe, etc.
    }
}
```

## Platform Considerations

- Windows: Uses WinSock2 API, guarded by `__WINNT__`. Requires `-lws2_32 -lwsock32`.
- Unix: POSIX APIs (poll, socket, fcntl). Platform abstraction lives in `ConnectionUtil.h/cpp` with cross-platform wrappers like `thorCreatePipe()`, `thorSetFDNonBlocking()`, `thorCloseSocket()`.
- `HAS_UNIQUE_EWOULDBLOCK` config flag handles platforms where EAGAIN == EWOULDBLOCK.
- Platform-specific macros: `THOR_POLL`, `THOR_SOCKET_ID`, `PAUSE_AND_WAIT` abstract differences.
