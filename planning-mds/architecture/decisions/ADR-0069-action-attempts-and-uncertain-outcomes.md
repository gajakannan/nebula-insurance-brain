# ADR-0069: Action Attempts Keep Their Identity and Uncertain Outcome

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-25
**Direction authorized by:** Operator, 2026-09-25. Formal acceptance waits for the proof gates below.
**Would refine:** [ADR-0028](ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md) (a retry policy for external side effects) and [ADR-0052](ADR-0052-delegated-agents-and-review-authority.md) (delegated action execution); complements [ADR-0041](ADR-0041-atomic-semantic-commit-and-projection-delivery.md), which covers internal commits
**Source:** Master blueprint sections 62, 64, 69, 91. Informed by Utopia decisions 0034 and 0050 (see References).

## Context

ADR-0041 makes internal semantic commits atomic and idempotent. External side effects are a different problem. Examples:

- an approved action calling a policy administration system;
- a notification;
- a webhook to a broker portal;
- a future MCP mutation tool.

Temporal (ADR-0028) retries activities by default. A synchronous "call, then record" shape cannot tell a request that was never sent from a remote effect whose response was lost. A retry can then repeat a non-idempotent effect, such as issuing an endorsement twice.

Utopia modelled this before building its action sender and found two tempting shortcuts that each produced duplicate dispatches:

- an ordinary nullable unique key;
- letting recovery take over a prepared attempt.

## Proposed Decision

### 1. An attempt has an identity before it has an effect

Each explicit user or approved-agent operation carries an `execution_request_id`, scoped to actor, action, and tenant/knowledge base.

- **Equal inputs under a new ID** are a new operation.
- **An existing ID with different inputs or a different definition revision** is a conflict.
- **A replay re-authorizes** before it reads back the attempt.
- **Uniqueness uses `NULLS NOT DISTINCT`,** which the PostgreSQL 18 build supports, and includes the action's identity.

### 2. A preview is bound to a revision

Every action definition edit and credential rotation increments the definition's revision in the same transaction.

- **Preview** returns the revision and a rendered request with no secrets, without dispatching.
- **Execution** renders from the same revision and validated arguments. It never uses a client-supplied URL, body, or header set.

### 3. Dispatch passes through explicit states

| State | Meaning |
|---|---|
| `PREPARED` | Intent persisted; no dispatch grant; replays only read it |
| `DISPATCHING` | A unique dispatch token and the authorization gate committed; only the original flow may send, and only after commit confirmation |
| `NOT_SENT` | Expiry or cancellation won atomically before dispatch |
| `RESPONSE_RECEIVED` | A response was observed (status, capture state, safe excerpt), independent of 2xx |
| `OUTCOME_UNKNOWN` | Dispatch may have happened and no durable observation establishes a response |

- **Recovery never turns `OUTCOME_UNKNOWN` into a sendable state.**
- **A late response** may update an unknown attempt using the original token. It never grants another send.
- **A lost commit acknowledgement means do not send.**
- **No database lock is held across the network.**
- **Revocation:** a revocation before the gate rejects the attempt; a revocation after it cannot recall the request.

### 4. No automatic retry of dispatch

- **Temporal activities that dispatch external effects** use a maximum of one attempt for the dispatch step, unless the remote contract honours an idempotency key that the attempt carries.
- **Internal, idempotent recomputation** may retry normally.
- **Redirects are not followed.**
- **HTTP 202 is a response, not proof of business completion.** A 500 may follow a remote effect.

### 5. A response is not a fact

A response is never written into canonical state directly. If it carries business information, that information enters as an observation through the normal assertion, review, and commit path, with `origin = SYSTEM_OBSERVATION`.

## Consequences

- **F0050** adopts the retry rule for external-effect activities.
- **F0059** executes approved actions through this state machine.
- **F0047's future mutation tools** and any webhook sender use it.
- **Retention** of attempts follows ADR-0043.
- **Audit** records the dispatch token, timestamps, and the immutable safe request snapshot.

## Proof gates before acceptance

- **Concurrent duplicate submissions** under one ID dispatch at most once.
- **Changing authorization or the definition revision** after preview rejects the attempt at the gate.
- **Process kills** after `PREPARED`, after `DISPATCHING`, and after the remote effect never produce a second dispatch, and leave the correct state.
- **Lost response bodies, timeouts, redirects, 202, and 500** are recorded as specified.
- **A Temporal activity replay** of an external-effect step does not re-send.

This supports **at-most-once application dispatch**. It does not provide exactly-once external business execution, which requires a remote contract the Brain cannot invent.

## References

Utopia at commit [`b3919ca`](https://github.com/deeplethe/utopia/tree/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a):

- [0050 — An action attempt keeps its identity and uncertain outcome](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0050-an-action-attempt-keeps-its-identity-and-uncertain-outcome.md)
- [0034 — An action is a declared call](https://github.com/deeplethe/utopia/blob/b3919ca8b4bf425cb4f65b507f9fd744b86c8e3a/docs/decisions/0034-an-action-is-a-declared-call.md)

Worked and boundary examples: [EX-SEM-011](../../examples/statements-time-and-governance.md#action-attempts).
