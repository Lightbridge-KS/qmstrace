# Changelog

## [Unreleased]

## [0.1.0] - 2026-11-02

### Added

- Independently packaged C# file, top-level statement, Razor and xUnit extraction using
  qmstrace API v1. Requires qmstrace 0.4.0 or later with API v1 support.
- Manifest-first registration of `csharp-file` and `xunit`; existing IDs, markers, digests,
  guidance and TRX run identities are preserved.
- Parser ownership: tree-sitter >=0.26,<0.27 and tree-sitter-c-sharp >=0.23.5,<0.24.
