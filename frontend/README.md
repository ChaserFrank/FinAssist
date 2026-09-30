# FinAssist Frontend

React (Vite) UI for FinAssist. Talks to the FastAPI backend documented in
`../docs/api.md`. This file also serves as the change log for adapting
Milkah's UI update to the real backend contract.

## Running locally

```bash
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
# open http://localhost:5173
```

The backend's default `CORS_ORIGINS` already allows this port. If you run
`npm run preview` instead (a different port), add that origin to the
backend's `CORS_ORIGINS` — see the root README.

## Pages

| Page | Backend calls | Notes |
|---|---|---|
| `SupportPage` (main) | `POST /api/v1/support/messages` | Free-text box, requires a customer reference. Uses the AI-interprets/orchestration-coordinates/backend-authorizes flow (`docs/ai.md`). |
| `PaymentLookupPage` | `GET /api/v1/transactions/{reference}`, `POST /api/v1/support/cases`, `GET /api/v1/support/cases/{reference}` | "Contact Support" opens a case; "Refresh case status" re-fetches it (there is no auto-investigate endpoint — see below). |
| `PaymentReversedPage` | `GET /api/v1/transactions/{reference}` | |
| `ReportPaymentIssuePage` | `POST /api/v1/support/cases` | |
| `CustomerVerificationPage` | `GET /api/v1/customers/{reference}` + `GET /api/v1/transactions/{reference}` | Ownership is checked client-side by comparing `transaction.customer_reference` to the looked-up customer — see `verifyCustomerOwnsTransaction` in `services/api.js`. No dedicated "verify" endpoint exists or was added. |
| `DisputePaymentPage` | Same verify, then `POST /api/v1/disputes` | The backend independently re-verifies ownership and eligibility when the dispute is actually created (ADR-005) — the client-side check is a UX convenience, not the security boundary. |

## Change log: adapting this UI update to the real backend

This update (from `frontend.zip`, 2026-09-29) was written against an
assumed API shape that had drifted from what the backend actually
implements. **No backend code was changed** — every fix below is
frontend-only, per the working agreement that the backend stays as the
source of truth. What was wrong and how it was fixed:

1. **`services/api.js` called endpoints that don't exist:**
   - `POST /api/v1/support/cases/{reference}/investigate` — there is no
     case-investigation/auto-resolve endpoint on the backend; a case's
     status only changes when a human agent updates it. Replaced with
     `GET /api/v1/support/cases/{reference}` (`getSupportCase`), used as a
     "refresh status" action rather than "trigger investigation."
   - `GET /api/v1/customers/{ref}/transactions/{ref}/verify` — there is no
     standalone ownership-verification endpoint. `GET /api/v1/transactions/
     {reference}` already returns `customer_reference`, so
     `verifyCustomerOwnsTransaction()` now does the comparison client-side
     using the two existing, already-tested endpoints. No backend addition
     needed.

2. **Field name / request shape mismatches on `POST /api/v1/support/cases`:**
   the UI sent `{transaction_reference, message}`; the backend requires
   `{customer_reference, category, description, transaction_reference?}`.
   Fixed in `createSupportCase()` and in every page that calls it
   (`PaymentLookupPage`, `ReportPaymentIssuePage`) — each of these pages
   now also collects a customer reference, since the backend needs one to
   authorize opening a case under an account.

3. **Response fields that don't exist:** `PaymentLookupPage` and
   `PaymentReversedPage` rendered a `payment.description` field that
   `GET /api/v1/transactions/{reference}` does not return (see
   `docs/api.md`). Removed those rows. `PaymentLookupPage` also displayed a
   fictitious `supportCase.response` field for a "RESOLVED" case with
   auto-generated text — removed along with the fake investigate flow
   above.

4. **Error handling parsed the wrong envelope:** the UI read
   `data?.detail` (a FastAPI-default shape); the backend returns
   `{"error": {"code", "message"}}` (`docs/api.md`). `request()` in
   `services/api.js` now reads `body.error.message`, and a new `ApiError`
   class exposes `.code` so pages can give specific, friendlier messages
   for `CUSTOMER_NOT_FOUND`, `TRANSACTION_NOT_FOUND`,
   `CUSTOMER_TRANSACTION_MISMATCH`, `DISPUTE_NOT_ELIGIBLE`, and
   `INVALID_TRANSACTION_STATE` instead of a generic failure message.

5. **`API_BASE_URL` was hardcoded** (`http://127.0.0.1:8000`) in both
   `services/api.js` and, duplicated, in `PaymentLookupPage.jsx` (which
   also bypassed `services/api.js` entirely and called `fetch` directly).
   Now reads `import.meta.env.VITE_API_BASE_URL` (see `.env.example`), and
   `PaymentLookupPage` uses the shared `services/api.js` helpers like every
   other page.

6. **The main `SupportPage`'s free-text box did nothing** (`onSubmit` was
   `console.log('Submitting:', message)`). Wired it to
   `POST /api/v1/support/messages` — the backend's most thoroughly tested
   feature (12 dedicated API tests, verified end-to-end with a real
   browser in earlier work) — with a customer-reference field and a result
   panel showing the outcome.

7. **Dead code removed:** `src/pages/SupportPage.jsx` was an earlier,
   unused draft (not imported anywhere — `App.jsx` imports `src/SupportPage.jsx`
   at the root instead). Deleted rather than left to confuse the next person.

8. **Missing CSS:** `.page-header` and `.customer-field` were referenced by
   several pages but had no rules in `index.css`. Added, matching the
   existing design tokens (`--text-primary`, `--border`, `--radius-sm`,
   etc.) — this is the one non-functional change in this pass.

9. **`Dockerfile` was a placeholder** (`echo "Frontend not yet
   implemented"`). Replaced with a real multi-stage build (Vite build →
   nginx). Not wired into the root `docker-compose.yml` (the frontend is
   still run separately, per the original architecture decision) but now
   actually buildable for later deployment.

## Verification

Every page was driven end-to-end through a real headless Chromium browser
against the real FastAPI backend and a real PostgreSQL database (not just
`npm run build` succeeding): free-text AI message → dispute created;
payment lookup → contact support → case status refresh; payment-reversed
check; issue report; payment verification for both a correct and an
incorrect owner, and an unknown customer; dispute creation, then a second
dispute on the same transaction correctly declined, then a dispute on a
`PENDING` transaction correctly declined — all rendering the right message
from the right backend error code, with zero unhandled console errors.
