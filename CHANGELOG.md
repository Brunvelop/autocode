# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses Git tags for release milestones.

## [0.1.0-alpha.1] - 2026-04-24

Initial public alpha release of **Autocode** as a minimalistic, registry-driven
framework for code quality and AI-assisted development.

### Added

- Registry-driven framework that exposes functions through API, CLI, MCP, and web interfaces.
- Unified application entrypoint via `autocode serve` with dashboard, docs, and generated interfaces.
- AI/chat capabilities including conversational chat, streaming chat, and context usage calculation.
- Code analysis features including structure summaries, metrics snapshots, architecture snapshots, and history views.
- Git/VCS tooling including repository tree, status, history, commit detail, and compact MCP-oriented summaries.
- Commit planning workflow with CRUD operations, execution flow, review states, approval, and revert support.
- MCP file operation tools for reading, writing, replacing, and deleting files.
- Web dashboard with chat, git dashboard, code dashboard, code explorer, and screen recorder components.
- Pytest plugin and standalone health-check command for code quality gates.

### Changed

- Migrated the framework layer to **Refract**, simplifying interfaces and app composition.
- Reworked planning/executor architecture into decomposed modules with pluggable backends.
- Simplified and hardened git execution, persistence, workflow transitions, and SSE streaming flow.
- Refined web components toward a composition-based architecture with improved dashboard navigation and UX.
- Aligned README and packaging metadata around the current Autocode architecture.

### Fixed

- Fixed streaming lifecycle, chat abort/disconnect behavior, and execution guards in the chat UI.
- Fixed plan execution robustness around heartbeats, persistence, revert/approve flow, and unexpected failures.
- Fixed dashboard and code explorer issues including refresh/navigation state problems and event-loop bugs.
- Fixed testing/plugin collection timing and static file/version edge cases.

### Documentation

- Rewrote major architecture and DCC documentation to match the current Refract-based design.
- Updated README to reflect the current product scope, commands, and usage model.

### Notes

- This is the first Git tag for the repository.
- The pre-release tag is intentionally marked as alpha while the project stabilizes its architecture and workflows.