import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewPanel } from "../ReviewPanel";
import type { ReviewItem } from "../types";

vi.mock("../Viewport", () => ({
  Viewport: ({ region }: { region: { page: number } | null }) =>
    <div data-testid="mock-viewport">{region?.page}</div>,
}));

const openItem: ReviewItem = {
  id: "item-1",
  type: "LOW_CONFIDENCE_ASSERTION",
  status: "open",
  assertion_id: "assertion-1",
  assertion_version: 1,
  tenant_id: "tenant-1",
  knowledge_base_id: "kb-1",
  review_batch_id: "batch-1",
  evidence: { source: "artifact-1", precision: "exact-span", selector: [] },
  decision: null,
  created_at: "2026-09-09T00:00:00Z",
};

describe("ReviewPanel", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/reviews/item-1") {
          return new Response(JSON.stringify(openItem), { status: 200 });
        }
        if (url.startsWith("/content/")) {
          return new Response(new ArrayBuffer(4), { status: 200 });
        }
        if (url === "/reviews/batches/batch-1/decisions") {
          return new Response(
            JSON.stringify({ decision_ids: ["d1"], applied: 1, duplicate: false, stale: 0, blocked: 0 }),
            { status: 200 },
          );
        }
        throw new Error(`unexpected fetch: ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads and renders the review item with its field list", async () => {
    render(<ReviewPanel reviewItemId="item-1" bearerToken="tok" />);

    await waitFor(() => expect(screen.getByTestId("review-panel")).toBeInTheDocument());
    expect(screen.getByTestId("field-list")).toBeInTheDocument();
  });

  it("submits a correction and shows the applied receipt", async () => {
    const user = userEvent.setup();
    render(<ReviewPanel reviewItemId="item-1" bearerToken="tok" />);
    await waitFor(() => expect(screen.getByTestId("field-list")).toBeInTheDocument());

    await user.type(screen.getByLabelText("Corrected value"), "$2,000,000");
    await user.click(screen.getByText("Correct"));

    await waitFor(() =>
      expect(screen.getByTestId("receipt-message")).toHaveTextContent("1 applied"),
    );
  });

  it("shows an error state when the review item fetch is denied", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ code: "not_found", title: "Not Found" }), { status: 404 })),
    );

    render(<ReviewPanel reviewItemId="item-1" bearerToken="tok" />);

    await waitFor(() => expect(screen.getByTestId("review-panel-error")).toBeInTheDocument());
    expect(screen.getByTestId("review-panel-error")).toHaveTextContent("not_found");
  });

  it("lets the reviewer inspect every supporting region and submits all selectors", async () => {
    const user = userEvent.setup();
    const selectors = [1, 2].map((page) => ({
      type: "nebula:BoxSelector", page, x0: 10, y0: 10, x1: 80, y1: 30,
    }));
    const item = { ...openItem, evidence: { ...openItem.evidence!, selector: selectors } };
    const fetcher = vi.fn(async (url: string) => {
      if (url === "/reviews/item-1") return new Response(JSON.stringify(item));
      if (url.startsWith("/content/")) return new Response(new ArrayBuffer(4));
      return new Response(JSON.stringify({ decision_ids: ["d1"], applied: 1, duplicate: false, stale: 0, blocked: 0 }));
    });
    vi.stubGlobal("fetch", fetcher);
    render(<ReviewPanel reviewItemId="item-1" bearerToken="tok" />);
    const chooser = await screen.findByLabelText("Evidence region");
    expect(screen.getByTestId("mock-viewport")).toHaveTextContent("1");
    await user.selectOptions(chooser, "1");
    expect(screen.getByTestId("mock-viewport")).toHaveTextContent("2");
    await user.click(screen.getByText("Accept"));
    await screen.findByTestId("receipt-message");
    const submission = vi.mocked(fetch).mock.calls.find(([url]) => String(url).endsWith("/decisions"));
    expect(JSON.parse(String(submission?.[1]?.body)).decisions[0].evidence.selector).toEqual(selectors);
  });
});
