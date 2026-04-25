# PRD: Tool Calling for Gemini Voice Agent

## Overview
Enable the Gemini voice agent to call external tools/APIs during conversations, allowing it to access real-time data and perform actions on behalf of the caller.

## Goals
- Extend agent capabilities beyond conversation to perform real-world actions
- Support dynamic decision-making based on external data
- Improve response accuracy with live information

## Core Features

### 1. Tool Integration
- Define available tools and their signatures (parameters, return types)
- Register tools with Gemini API
- Support case retrieval tool:
  - Query insurance/case database by phone number or claim ID
  - Fetch case details (claimant info, incident type, status)

### 2. Tool Calling Flow
- Agent detects when tool call is needed based on user request
- Extract tool name and parameters from Gemini response
- Execute tool to retrieve case data
- **Update application state with retrieved data** (caseId, claimantInfo, incident type, etc.)
- Agent uses state data for subsequent conversation turns and decision-making

### 3. State Management
- Define case data schema in state
- Populate state fields from tool results:
  - `case_id`: Unique case identifier
  - `claimant_info`: Name, contact details, policy number
  - `incident_type`: Type of claim (accident, theft, etc.)
  - `case_status`: Current case status
  - `incident_details`: Extracted from tool response
- Make state available to agent for context in subsequent turns

### 4. Error Handling
- Handle tool failures gracefully
- Provide fallback responses when tools unavailable
- Log failures for debugging

## Implementation Notes
- Use Gemini's `functionCalling` or `toolUse` capability
- Implement request/response validation
- Add logging for all tool calls and responses
- Consider rate limiting and timeout policies

## Acceptance Criteria
- [ ] Case retrieval tool callable by agent (lookup by phone/claim ID)
- [ ] Retrieved case data successfully populates state
- [ ] Agent can access and reference state data in subsequent responses
- [ ] State persists across conversation turns
- [ ] Tool calls properly logged with inputs/outputs
- [ ] Agent gracefully handles tool failures without crash
- [ ] Response latency acceptable (<2s additional per tool call)
