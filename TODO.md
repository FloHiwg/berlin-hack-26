# TODO

## Reliability

- [ ] Session reconnection: save claim state and re-attach when Gemini hits the 15-min session limit
- [ ] Retry / graceful shutdown on Twilio WebSocket disconnect mid-call

## Observability

- [ ] Record conversations: save full transcript (both sides) to `storage/sessions/<id>_transcript.txt` for every session
- [ ] Latency logging: log time from end-of-speech to first agent audio chunk per turn to `storage/sessions/<id>_latency.jsonl`

## Eval

- [ ] Run all three eval scenarios and make them pass reliably
  - `evals/happy_path.yaml`
  - `evals/third_party_caller.yaml`
  - `evals/escalation.yaml`
- [ ] Add eval scenario: caller corrects a field mid-flow (e.g., wrong date)
- [ ] Add eval scenario: caller identifies by name + DOB (not policy number)

## Playbook

- [ ] Tune `FIELD_EXPECTATIONS` based on real call transcripts once recording is in place
- [ ] Add `handoff_required` assertion to escalation eval (field exists in ClaimState but is not yet set by the `escalate` tool call reliably)

## Phone

- [ ] End-to-end phone test: call Twilio number, complete full intake, verify saved JSON
- [ ] `POST /twilio/status` — forward call lifecycle events to a log file, not just stdout
