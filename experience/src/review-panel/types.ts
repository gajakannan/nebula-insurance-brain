// Mirrors planning-mds/api/brain-api.yaml's ReviewItem/EvidenceLocator/ReviewDecision
// schemas (F0001-S0004). Kept in this one file rather than generated from the OpenAPI
// document — F0015 (compiled contracts) is where that generation lands.

export type Precision = "exact-span" | "table-cell" | "block" | "page" | "document" | "unresolved";

export interface Selector {
  type: string;
  [key: string]: unknown;
}

export interface EvidenceLocator {
  source: string;
  precision: Precision;
  part?: string | null;
  unresolved_reason?: string | null;
  selector: Selector[];
}

export type ReviewDecisionAction = "ACCEPT" | "CORRECT" | "REJECT" | "BLOCKED";

export type ReviewDecisionReasonCode =
  | "MISREAD_VALUE"
  | "WRONG_REGION"
  | "NOT_IN_SOURCE"
  | "OUT_OF_SCOPE"
  | "EVIDENCE_UNRESOLVED";

export interface ReviewDecision {
  id: string;
  review_item_id: string;
  review_batch_id: string;
  action: ReviewDecisionAction;
  reason_code: ReviewDecisionReasonCode | null;
  corrected_value: Record<string, unknown> | null;
  corrected_assertion_id: string | null;
  evidence: EvidenceLocator | null;
  reviewer_principal_id: string;
  reviewer_comment: string | null;
  decided_at: string;
  assertion_version: number;
  stale: boolean;
  event_sha256: string;
}

export interface ReviewItem {
  id: string;
  type: string;
  status: "open" | "in_review" | "decided" | "stale" | "blocked";
  assertion_id: string;
  assertion_version: number;
  tenant_id: string;
  knowledge_base_id: string;
  review_batch_id: string | null;
  evidence: EvidenceLocator | null;
  decision: ReviewDecision | null;
  created_at: string;
}

export interface ReviewDecisionReceipt {
  decision_ids: string[];
  applied: number;
  duplicate: boolean;
  stale: number;
  blocked: number;
}
