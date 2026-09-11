import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Viewport } from "../Viewport";

const mockPage = {
  getViewport: () => ({ width: 100, height: 200 }),
  render: () => ({ promise: Promise.resolve() }),
};

vi.mock("pdfjs-dist", () => ({
  GlobalWorkerOptions: {},
  getDocument: () => ({
    promise: Promise.resolve({
      numPages: 3,
      getPage: () => Promise.resolve(mockPage),
    }),
  }),
}));

describe("Viewport", () => {
  it("renders the page count once the document loads", async () => {
    render(<Viewport pdfBytes={new ArrayBuffer(4)} region={null} precisionIsExact={false} />);

    await waitFor(() => expect(screen.getByText("1 / 3")).toBeInTheDocument());
  });

  it("draws an exact-span overlay region on the matching page", async () => {
    render(
      <Viewport
        pdfBytes={new ArrayBuffer(4)}
        region={{ page: 1, x0: 10, y0: 10, x1: 50, y1: 30 }}
        precisionIsExact={true}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("evidence-region")).toBeInTheDocument());
    expect(screen.queryByTestId("page-level-banner")).not.toBeInTheDocument();
  });

  it("shows a page-level banner instead of a tight box when precision is not exact", async () => {
    render(
      <Viewport
        pdfBytes={new ArrayBuffer(4)}
        region={{ page: 1, x0: 0, y0: 0, x1: 0, y1: 0 }}
        precisionIsExact={false}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("page-level-banner")).toBeInTheDocument());
    expect(screen.queryByTestId("evidence-region")).not.toBeInTheDocument();
  });
});
