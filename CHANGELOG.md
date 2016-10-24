# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [0.2.4] - 2016-10-24
### Fixed
- Install no longer requires Cython

## [0.2.3] - 2016-07-15
### Changed
- Intensive encoding operations now release the GIL.

## [0.2.2] - 2016-07-14
### Fixed
- GCC compilation missing -std=c99

## [0.2.1] - 2016-07-14
### Added
- More extensive documentation

### Changed
- C bindings to Cython bindings

### Fixed
- Decoding including junk data on large files.

## [0.2.0] - 2016-07-05
### Added
- window_sz2 and lookahead_sz2 parameters for encode/decode functions.
- automated benchmarks

### Fixed
- Performance of encoding/decoding large files
- Compilation for python 3 (still not fully working)

[Unreleased]: https://github.com/johan-sports/pyheatshrink/compare/0.2.4...HEAD
[0.2.4]: https://github.com/johan-sports/pyheatshrink/compare/0.2.3...0.2.4
[0.2.3]: https://github.com/johan-sports/pyheatshrink/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/johan-sports/pyheatshrink/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/johan-sports/pyheatshrink/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/johan-sports/pyheatshrink/compare/0.1.2...0.2.0
