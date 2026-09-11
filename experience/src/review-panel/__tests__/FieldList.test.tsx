import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FieldList } from "../FieldList";
import type { ReviewItem } from "../types";

function makeItem(overrides: Partial<ReviewItem> = {}): ReviewItem {
  return {
    id: "item-1",
    type: "LOW_CONFIDENCE_ASSERTION",
    status: "open",
    assertion_id: "assertion-1",
    assertion_version: 1,
    tenant_id: "tenant-1",
    knowledge_base_id: "kb-1",
    review_batch_id: "batch-1",
    evidence: {
      source: "artifact-1",
      precision: "exact-span",
      selector: [],
    },
    decision: null,
    created_at: "2026-09-09T00:00:00Z",
    ...overrides,
  };
}

describe("FieldList", () => {
  it("shows accept/correct/reject actions when evidence is resolved", () => {
    render(<FieldList item={makeItem()} disabled={false} onDecide={vi.fn()} />);

    expect(screen.getByTestId("field-list")).toBeInTheDocument();
    expect(screen.getByText("Accept")).toBeInTheDocument();
    expect(screen.getByText("Correct")).toBeInTheDocument();
    expect(screen.getByText("Reject")).toBeInTheDocument();
  });

  it("disables Correct until a value is typed", async () => {
    const user = userEvent.setup();
    render(<FieldList item={makeItem()} disabled={false} onDecide={vi.fn()} />);

    expect(screen.getByText("Correct")).toBeDisabled();
    await user.type(screen.getByLabelText("Corrected value"), "$2,000,000");
    expect(screen.getByText("Correct")).not.toBeDisabled();
  });

  it("calls onDecide with CORRECT and the typed value", async () => {
    const user = userEvent.setup();
    const onDecide = vi.fn();
    render(<FieldList item={makeItem()} disabled={false} onDecide={onDecide} />);

    await user.type(screen.getByLabelText("Corrected value"), "$2,000,000");
    await user.click(screen.getByText("Correct"));

    expect(onDecide).toHaveBeenCalledWith({
      action: "CORRECT",
      reasonCode: "MISREAD_VALUE",
      correctedValue: { value: "$2,000,000" },
    });
  });

  it("offers only a blocked action, no accept/correct, when evidence is unresolved", () => {
    const item = makeItem({
      evidence: { source: "artifact-1", precision: "unresolved", unresolved_reason: "no text layer", selector: [] },
    });
    render(<FieldList item={item} disabled={false} onDecide={vi.fn()} />);

    expect(screen.getByTestId("field-list-unresolved")).toBeInTheDocument();
    expect(screen.queryByText("Accept")).not.toBeInTheDocument();
    expect(screen.queryByText("Correct")).not.toBeInTheDocument();
    expect(screen.getByText("Record blocked")).toBeInTheDocument();
  });

  it("shows the recorded decision instead of actions once decided", () => {
    const item = makeItem({
      decision: {
        id: "d1",
        review_item_id: "item-1",
        review_batch_id: "batch-1",
        action: "CORRECT",
        reason_code: "MISREAD_VALUE",
        corrected_value: { value: "$2,000,000" },
        corrected_assertion_id: "assertion-2",
        evidence: null,
        reviewer_principal_id: "principal-1",
        reviewer_comment: null,
        decided_at: "2026-09-09T00:00:00Z",
        assertion_version: 1,
        stale: false,
        event_sha256: "a".repeat(64),
      },
    });
    render(<FieldList item={item} disabled={false} onDecide={vi.fn()} />);

    expect(screen.getByTestId("field-list-decided")).toBeInTheDocument();
    expect(screen.getByText(/CORRECT/)).toBeInTheDocument();
  });
});
