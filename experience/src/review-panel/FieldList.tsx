import { useState } from "react";
import type { ReviewDecisionAction, ReviewDecisionReasonCode, ReviewItem } from "./types";

export interface FieldDecision {
  action: ReviewDecisionAction;
  reasonCode?: ReviewDecisionReasonCode;
  correctedValue?: Record<string, unknown>;
}

interface FieldListProps {
  item: ReviewItem;
  disabled: boolean;
  onDecide: (decision: FieldDecision) => void;
}

/** Proof-scope field list: one field per review item (the low-confidence assertion).
 * F0022 generalizes this to a real multi-field list inside Document 360. */
export function FieldList({ item, disabled, onDecide }: FieldListProps) {
  const [draftValue, setDraftValue] = useState("");
  const unresolved = item.evidence?.precision === "unresolved";

  if (item.decision) {
    return (
      <div data-testid="field-list-decided">
        <p>
          Decision recorded: <strong>{item.decision.action}</strong>
          {item.decision.reason_code ? ` (${item.decision.reason_code})` : ""}
        </p>
      </div>
    );
  }

  if (unresolved) {
    return (
      <div data-testid="field-list-unresolved">
        <p>
          Evidence could not be anchored ({item.evidence?.unresolved_reason ?? "reason not given"}).
          No accept or correct action is available for this field (ADR-0058).
        </p>
        <button
          disabled={disabled}
          onClick={() =>
            onDecide({ action: "BLOCKED", reasonCode: "EVIDENCE_UNRESOLVED" })
          }
        >
          Record blocked
        </button>
      </div>
    );
  }

  return (
    <div data-testid="field-list">
      <label>
        Corrected value
        <input
          type="text"
          value={draftValue}
          onChange={(event) => setDraftValue(event.target.value)}
          disabled={disabled}
        />
      </label>
      <div className="field-actions">
        <button disabled={disabled} onClick={() => onDecide({ action: "ACCEPT" })}>
          Accept
        </button>
        <button
          disabled={disabled || !draftValue}
          onClick={() =>
            onDecide({
              action: "CORRECT",
              reasonCode: "MISREAD_VALUE",
              correctedValue: { value: draftValue },
            })
          }
        >
          Correct
        </button>
        <button
          disabled={disabled}
          onClick={() => onDecide({ action: "REJECT", reasonCode: "NOT_IN_SOURCE" })}
        >
          Reject
        </button>
      </div>
    </div>
  );
}
