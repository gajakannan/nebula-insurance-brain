import type { ReviewDecisionAction, ReviewDecisionReasonCode, ReviewDecisionReceipt, ReviewItem } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ code: "unknown", title: response.statusText }));
    throw new ApiError(response.status, body.code ?? "unknown", body.title ?? response.statusText);
  }
  return (await response.json()) as T;
}

export async function fetchReviewItem(reviewItemId: string, bearerToken: string): Promise<ReviewItem> {
  const response = await fetch(`/reviews/${reviewItemId}`, {
    headers: { Authorization: `Bearer ${bearerToken}` },
  });
  return handle<ReviewItem>(response);
}

export interface SubmitDecisionInput {
  reviewItemId: string;
  action: ReviewDecisionAction;
  assertionVersion: number;
  reasonCode?: ReviewDecisionReasonCode;
  correctedValue?: Record<string, unknown>;
  evidence?: ReviewItem["evidence"];
  reviewerComment?: string;
}

export async function submitReviewDecisions(
  reviewBatchId: string,
  decisions: SubmitDecisionInput[],
  bearerToken: string,
): Promise<ReviewDecisionReceipt> {
  const response = await fetch(`/reviews/batches/${reviewBatchId}/decisions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${bearerToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      decisions: decisions.map((decision) => ({
        review_item_id: decision.reviewItemId,
        action: decision.action,
        assertion_version: decision.assertionVersion,
        reason_code: decision.reasonCode ?? null,
        corrected_value: decision.correctedValue ?? null,
        evidence: decision.evidence ?? null,
        reviewer_comment: decision.reviewerComment ?? null,
      })),
    }),
  });
  return handle<ReviewDecisionReceipt>(response);
}
