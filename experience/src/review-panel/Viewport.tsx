import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";

// pdf.js needs its worker script served as a URL; Vite resolves this to a hashed
// asset at build time (F0001-S0004: "the panel makes no third-party network
// request" — the worker ships in the bundle, never fetched from a CDN).
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url,
).toString();

const RENDER_SCALE = 1.5;

export interface RegionBox {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

interface ViewportProps {
  pdfBytes: ArrayBuffer | null;
  region: RegionBox | null;
  /** Honest rendering of ADR-0058: a page-level ground draws a page-level mark,
   * never a tight box the evidence does not support. */
  precisionIsExact: boolean;
}

export function Viewport({ pdfBytes, region, precisionIsExact }: ViewportProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pageCount, setPageCount] = useState(0);

  useEffect(() => {
    if (!pdfBytes) {
      setDoc(null);
      return;
    }
    let cancelled = false;
    const loadingTask = pdfjsLib.getDocument({ data: pdfBytes.slice(0) });
    loadingTask.promise.then((loaded) => {
      if (cancelled) return;
      setDoc(loaded);
      setPageCount(loaded.numPages);
    });
    return () => {
      cancelled = true;
    };
  }, [pdfBytes]);

  useEffect(() => {
    if (region) setPageNumber(region.page);
  }, [region]);

  useEffect(() => {
    if (!doc || !canvasRef.current) return;
    let cancelled = false;
    const canvas = canvasRef.current;
    doc.getPage(pageNumber).then(async (page) => {
      if (cancelled) return;
      const viewport = page.getViewport({ scale: RENDER_SCALE });
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const context = canvas.getContext("2d");
      if (!context) return;
      await page.render({ canvasContext: context, viewport }).promise;
    });
    return () => {
      cancelled = true;
    };
  }, [doc, pageNumber]);

  const showOverlay = region !== null && region.page === pageNumber;
  const overlayBox = showOverlay
    ? precisionIsExact
      ? {
          left: region!.x0 * RENDER_SCALE,
          top: region!.y0 * RENDER_SCALE,
          width: (region!.x1 - region!.x0) * RENDER_SCALE,
          height: (region!.y1 - region!.y0) * RENDER_SCALE,
        }
      : null // page-level: no tight box, see the page-level banner instead
    : null;

  return (
    <div data-testid="review-viewport" style={{ position: "relative", display: "inline-block" }}>
      <div className="viewport-toolbar">
        <button onClick={() => setPageNumber((p) => Math.max(1, p - 1))} disabled={pageNumber <= 1}>
          ← Page
        </button>
        <span>
          {pageNumber} / {pageCount || "–"}
        </span>
        <button
          onClick={() => setPageNumber((p) => Math.min(pageCount, p + 1))}
          disabled={pageNumber >= pageCount}
        >
          Page →
        </button>
      </div>
      {showOverlay && !precisionIsExact && (
        <div data-testid="page-level-banner" className="page-level-banner">
          Page-level evidence only — no tight region drawn
        </div>
      )}
      <canvas ref={canvasRef} data-testid="pdf-canvas" />
      {overlayBox && (
        <div
          data-testid="evidence-region"
          className="evidence-region"
          style={{ position: "absolute", pointerEvents: "none", ...overlayBox, border: "2px solid" }}
        />
      )}
    </div>
  );
}
