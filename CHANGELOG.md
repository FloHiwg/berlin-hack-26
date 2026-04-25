# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Tool Calling Feature**: Implement `retrieve_case_data` tool to query insurance case database by phone number or claim ID
  - Agent can now retrieve existing case data at the start of a session
  - Retrieved data automatically populates the claim state with customer info, incident details, and third-party information
  - Mock database with sample cases for testing
  - Added comprehensive tests for case retrieval and state population
- System prompt updated to instruct agent to call `retrieve_case_data` at session start

## [0.1.0] - 2024-04-25

- Initial release with Phase 3 implementation
- Identity verification with OR logic
- Caller verification and conditional stages
- Playbook engine with evaluation runner
