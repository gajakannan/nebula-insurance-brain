import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchReviewItem, submitReviewDecisions } from "./api";
import { FieldList, type FieldDecision } from "./FieldList";
import type { RegionBox } from "./Viewport";
import { Viewport } from "./Viewport";
import type { ReviewItem } from "./types";

interface ReviewPanelProps {
  reviewItemId: string;
  bearerToken: string;
}

function regionFromSelector(item: ReviewItem, index: number): RegionBox | null {
  const selector = item.evidence?.selector?.filter((s) => s.type === "nebula:BoxSelector")[index];
  if (!selector || typeof selector.page !== "number") return null;
  const { page, x0, y0, x1, y1 } = selector as Record<string, number>;
  if ([x0, y0, x1, y1].some((v) => typeof v !== "number")) {
    return { page, x0: 0, y0: 0, x1: 0, y1: 0 };
  }
  return { page, x0, y0, x1, y1 };
}

export function ReviewPanel({ reviewItemId, bearerToken }: ReviewPanelProps) {
  const [item, setItem] = useState<ReviewItem | null>(null);
  const [pdfBytes, setPdfBytes] = useState<ArrayBuffer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [receiptMessage, setReceiptMessage] = useState<string | null>(null);
  const [regionIndex, setRegionIndex] = useState(0);

  const load = useCallback(async () => {
    setError(null);
    try {
      const loaded = await fetchReviewItem(reviewItemId, bearerToken);
      setItem(loaded);
      setRegionIndex(0);
      if (loaded.evidence?.source) {
        const response = await fetch(`/content/${loaded.evidence.source}/files/source.pdf`, {
          headers: { Authorization: `Bearer ${bearerToken}` },
        });
        if (response.ok) {
          setPdfBytes(await response.arrayBuffer());
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.code}: ${err.message}`);
      } else {
        setError(String(err));
      }
    }
  }, [reviewItemId, bearerToken]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDecide(decision: FieldDecision) {
    if (!item || !item.review_batch_id) return;
    setSubmitting(true);
    setReceiptMessage(null);
    try {
      const receipt = await submitReviewDecisions(
        item.review_batch_id,
        [
          {
            reviewItemId: item.id,
            action: decision.action,
            assertionVersion: item.assertion_version,
            reasonCode: decision.reasonCode,
            correctedValue: decision.correctedValue,
            evidence: item.evidence,
          },
        ],
        bearerToken,
      );
      if (receipt.duplicate) {
        setReceiptMessage("Already submitted — no change (idempotent resubmission).");
      } else if (receipt.stale > 0) {
        setReceiptMessage("This assertion changed since the batch was assembled — a new review item was opened.");
      } else {
        setReceiptMessage(`Recorded: ${receipt.applied} applied, ${receipt.blocked} blocked.`);
      }
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.code}: ${err.message}` : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (error) {
    return <div data-testid="review-panel-error">{error}</div>;
  }
  if (!item) {
    return <div data-testid="review-panel-loading">Loading…</div>;
  }

  const regions = item.evidence?.selector?.filter((s) => s.type === "nebula:BoxSelector") ?? [];
  const region = regionFromSelector(item, regionIndex);
  const precisionIsExact = item.evidence?.precision === "exact-span" || item.evidence?.precision === "table-cell";

  return (
    <div data-testid="review-panel" className="review-panel">
      <aside className="artifact-rail" data-testid="artifact-rail">
        <p>Artifact: {item.evidence?.source ?? "none"}</p>
      </aside>
      <main>
        {regions.length > 1 && (
          <label>
            Evidence region
            <select aria-label="Evidence region" value={regionIndex}
              onChange={(event) => setRegionIndex(Number(event.target.value))}>
              {regions.map((selector, index) => (
                <option key={index} value={index}>
                  Region {index + 1} of {regions.length} — page {String(selector.page ?? "unknown")}
                </option>
              ))}
            </select>
          </label>
        )}
        <Viewport pdfBytes={pdfBytes} region={region} precisionIsExact={precisionIsExact} />
      </main>
      <section className="field-panel" data-testid="field-panel">
        <FieldList item={item} disabled={submitting} onDecide={handleDecide} />
        {receiptMessage && <p data-testid="receipt-message">{receiptMessage}</p>}
      </section>
    </div>
  );
}
