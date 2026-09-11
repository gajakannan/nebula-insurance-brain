import { useState } from "react";
import { ReviewPanel } from "./review-panel/ReviewPanel";

/** Proof-scope entry point: reads the review item and a bearer token from the URL
 * (`?reviewItemId=...&token=...`), or a form when absent. F0021 replaces this with
 * the real OIDC session shell and routing. */
export function App() {
  const params = new URLSearchParams(window.location.search);
  const [reviewItemId, setReviewItemId] = useState(params.get("reviewItemId") ?? "");
  const [token, setToken] = useState(params.get("token") ?? "");
  const [started, setStarted] = useState(Boolean(params.get("reviewItemId") && params.get("token")));

  if (!started) {
    return (
      <form
        data-testid="proof-scope-launch-form"
        onSubmit={(event) => {
          event.preventDefault();
          setStarted(true);
        }}
      >
        <h1>Nebula Review Panel (proof scope)</h1>
        <label>
          Review item id
          <input value={reviewItemId} onChange={(event) => setReviewItemId(event.target.value)} />
        </label>
        <label>
          Bearer token
          <input value={token} onChange={(event) => setToken(event.target.value)} />
        </label>
        <button type="submit">Open</button>
      </form>
    );
  }

  return <ReviewPanel reviewItemId={reviewItemId} bearerToken={token} />;
}
