# Later semantic examples

All examples below are conceptual, synthetic, and unimplemented. They extend EX-GL-001 without changing its v0.1 scope. The [coverage map](README.md) links owners and the glossary supplies definitions.

## Retrieval projection

**EX-FUTURE-001 — F0033/F0035, v0.2A.** A question about an each-occurrence limit retrieves a semantically similar policy passage. Its embedding record links the source ID, tenant/KB, model and version, embedding version/dimension, and authorization metadata. A retrieval score ranks relevance. The system must still resolve the requested policy, scope, time, accepted facts, and authorized evidence before answering.

**Boundary:** The nearest passage belongs to a different policy or describes an aggregate limit. High similarity cannot substitute that value for EX-COV-001's each-occurrence fact. An entity/fact/vector composite view is useful, but the vector can be rebuilt without changing the canonical fact or its history.

## Learning candidate

**EX-FUTURE-002 — F0041/F0042, v0.2B; F0060 reasoning-pattern promotion, v0.4+.** Repeated questions suggest a new “guideline exception rationale” concept. Record a LearningCandidate with supporting independent evidence, scope, owner, and proposed ontology change. A steward reviews it before a release can change extraction or reasoning.

**Boundary:** Ten paraphrases of one model guess are not ten independent sources. A candidate rule never becomes executable merely because the model repeats it. v0.1's reviewed fixed guideline releases do not constitute autonomous learning.

## Normative obligation

**EX-FUTURE-003 — F0052, v0.3.** A fictional operations policy says a bound policy must be issued within 24 hours. Store the obligation's condition, required event, authority, valid interval, and version separately from observed issuance facts.

**Boundary:** The obligation does not imply that issuance happened. Missing issuance evidence is not automatically a proven violation without the defined completeness, observation-window, and exception semantics. `requiresProof` similarly describes an obligation; `supportedBy` points to actual evidence. F0065 does not implement a general obligation engine.

## Hypothetical scenario

**EX-FUTURE-004 — F0053, v0.3.** An analyst asks what the guideline comparison would be if the each-occurrence limit were USD 2,000,000 before any endorsement is accepted. Create a scenario with a base snapshot and an explicit assumption override; its assessment is labeled hypothetical.

**Boundary:** The scenario must not overwrite the accepted USD 500,000 fact or make the hypothetical result appear in a canonical “what applied then?” query. Using a newer guideline to reassess an earlier knowledge snapshot is also a scenario, not historical reconstruction. F0065 history uses only rule releases available at the requested known time.
