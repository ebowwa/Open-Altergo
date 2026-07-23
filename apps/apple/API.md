# Apple API contract

This document separates the API that exists now from future contracts. Swift
must be implemented against the current section only. Proposed endpoints must
not leak into shipping UI until their server tests exist.

## 1. Existing HTTP API

Source of truth:

- `apis/http_api/app.py`
- `tests/test_http_api.py`
- `cloud/engine/src/pipeline.py`

### Health

```http
GET /health
```

```json
{
  "status": "ok",
  "model_loaded": false
}
```

`model_loaded` reports lazy model state. `false` is not an unhealthy server.

### Create transcription

```http
POST /v1/transcriptions
Content-Type: multipart/form-data
```

Fields:

| Field | Type | Required | Default | Constraint |
| --- | --- | --- | --- | --- |
| `video` | file | yes | — | non-empty, at most 250 MB |
| `hflip` | boolean text | no | `false` | mirror/unmirror preprocessing |
| `nbest` | integer text | no | `5` | 1 through 40 |
| `max_seconds` | integer text | no | `40` | 1 through 120 |

Recognized filename suffixes are `.mp4`, `.mov`, `.m4v`, and `.webm`. Other
suffixes are treated as `.mp4` server-side; the client should still send a
truthful supported filename and MIME type.

Representative success:

```json
{
  "segments": [
    {
      "seg_frames": [0, 75],
      "seg_time": [0.0, 3.0],
      "text": "hello world",
      "nbest": [
        {"text": "HELLO WORLD", "score": -1.23},
        {"text": "YELLOW WORLD", "score": -2.17}
      ]
    }
  ],
  "transcript": "hello world",
  "n_segments": 1
}
```

No face detected:

```json
{
  "segments": [],
  "transcript": "",
  "n_segments": 0,
  "no_face": true
}
```

The server may return fewer alternatives than requested. Beam scores are model
ranking values, not calibrated probabilities. The UI must call them
"alternatives," not confidence percentages.

Current error shapes use FastAPI's `detail`:

```json
{"detail": "Uploaded video is empty"}
```

Expected status handling:

| Status | Meaning | iOS behavior |
| --- | --- | --- |
| 200 | decoded result | display result or no-face guidance |
| 400 | invalid/empty video or preprocessing error | explain and allow retake |
| 413 | over 250 MB | reject before upload when possible |
| 422 | invalid form option | treat as client/configuration defect |
| 5xx | inference/server failure | retryable user-facing server error |
| network | offline, TLS, DNS, timeout, cancellation | typed, distinct behavior |

The current endpoint exposes no authentication, idempotency key, request ID,
job status, resumable upload, or formal OpenAPI-pinned schema. Those are known
gaps, not fields for the client to guess.

## 2. Swift models

Use explicit coding keys and tolerant additive decoding:

```swift
struct HealthResponse: Decodable, Sendable, Equatable {
    let status: String
    let modelLoaded: Bool
}

struct TranscriptionResponse: Decodable, Sendable, Equatable {
    let segments: [TranscriptSegment]
    let transcript: String
    let segmentCount: Int
    let noFace: Bool
}

struct TranscriptSegment: Decodable, Sendable, Equatable, Identifiable {
    let frameRange: FrameRange
    let timeRange: TimeRange
    let text: String
    let alternatives: [TranscriptAlternative]
}

struct TranscriptAlternative: Decodable, Sendable, Equatable {
    let text: String
    let score: Double
}
```

`noFace` defaults to `false` when omitted. Validate every two-element range;
do not rely on unchecked array subscripts in UI code. Preserve raw score only
for ordering and diagnostics.

Create checked-in fixtures for:

- health with model loaded and unloaded;
- one segment and several alternatives;
- multiple segments;
- no face;
- empty transcript without `no_face`;
- unknown additive response fields;
- malformed range;
- FastAPI error detail; and
- 413 and 422 errors.

Contract tests must compare fixture shape with Python API tests. When the server
changes incompatibly, update server tests, this document, fixtures, and Swift
decoding in one reviewed change.

## 3. Multipart requirements

The encoder must:

- use a cryptographically random boundary;
- escape quoted disposition values;
- write scalar fields as UTF-8;
- stream/copy the video from its file URL into a temporary multipart file;
- use CRLF delimiters;
- close the final boundary;
- report the final content length;
- delete the multipart file on success, failure, and cancellation; and
- be byte-for-byte unit tested with a fixed boundary and tiny fixture.

Do not use a single in-memory `Data` buffer for the full body.

## 4. Proposed production hardening

Before external TestFlight, design and test:

- user/device authentication;
- request IDs returned in headers;
- rate-limit status and retry metadata;
- stable machine-readable error codes;
- server-side duration and content-type inspection;
- idempotency or asynchronous transcription jobs;
- privacy/retention policy enforcement; and
- a versioned OpenAPI artifact checked by both Python and Swift CI.

An asynchronous job contract is preferable if production inference regularly
outlives foreground execution:

```text
POST /v1/transcription-jobs  -> 202 + job ID
PUT  signed upload URL       -> media
GET  /v1/transcription-jobs/{id}
DELETE /v1/transcription-jobs/{id}
```

That is a future migration, not the MVP contract.

## 5. Proposed personalization API

These endpoints do not exist:

```text
POST   /v1/personalization/sessions
GET    /v1/personalization/sessions/{session_id}
POST   /v1/personalization/sessions/{session_id}/examples
DELETE /v1/personalization/sessions/{session_id}/examples/{example_id}
POST   /v1/personalization/training-jobs
GET    /v1/personalization/training-jobs/{job_id}
POST   /v1/personalization/models/{model_id}/activate
DELETE /v1/personalization/models/{model_id}
GET    /v1/personalization/export
DELETE /v1/personalization/data
```

An example upload binds:

- authenticated user;
- server-issued session ID;
- server-issued prompt ID and prompt-set revision;
- exact expected text;
- clip metadata such as duration, orientation, and capture build;
- explicit consent policy version; and
- a client-generated idempotency key.

The server, not the app, owns train/validation/test assignment. Split by
recording session or date so visually adjacent clips do not leak across sets.

Corrections remain local unless the user taps a separate action such as "Use
this correction for my personalized model" and the server records that consent.
General model training requires another distinct authorization.
