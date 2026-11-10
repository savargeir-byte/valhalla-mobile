# Valhalla patches for iOS 16

`src/valhalla` is the upstream submodule. `scripts/build_apple.sh` applies
`valhalla-*.patch` before configuring, so every iOS slice is built from the
patched source.

## valhalla-costmatrix-no-pmr.patch

`thor::CostMatrix::ReachedMap` used `std::pmr::unsynchronized_pool_resource`
and `std::pmr::polymorphic_allocator`. Apple's libc++ ships the pmr runtime
only from iOS 17.0, so an app that links it is killed by dyld at launch on
iOS 16 (`Symbol not found: __ZNSt3__13pmr15memory_resourceD2Ev`) even when
CostMatrix is never called. The patch keeps the same map and vector, with
the default allocator. It only changes where memory comes from.

## Deployment target 16.5

Valhalla formats floats with `std::format`, which calls the floating-point
`std::to_chars` overloads. These are in the OS libc++ from iOS 16.5, so the
package, the triplets and `build_apple.sh` declare 16.5 instead of 16.4.
`-Werror=unguarded-availability-new` turns any newer API into a build error.

## Build

`.github/workflows/goice-ios16.yml` (manual) builds the three iOS slices,
audits every slice with `scripts/audit_ios_libcxx.py`, runs the routing and
matrix tests on the simulator, and attests the zip. It publishes nothing.
