// Base URL of the FinAssist backend. Configurable via Vite env (VITE_*
// variables are the only ones exposed to browser code) so the same build
// can point at different environments without a code change.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

// Mirrors the backend's ErrorCode values (backend/app/core/exceptions.py)
// so callers can branch on a stable code instead of parsing message text.
export class ApiError extends Error {
  constructor(message, { code, status } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  // 204 / empty bodies never happen on this API today, but don't blow up if
  // one ever does.
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    // Every FinAssist error response uses the envelope:
    //   { "error": { "code": "...", "message": "..." } }
    // (see docs/api.md) -- including FastAPI's own request-validation
    // errors, which the backend maps onto the same shape.
    const code = body?.error?.code
    const message = body?.error?.message || `Request failed (HTTP ${response.status})`
    throw new ApiError(message, { code, status: response.status })
  }

  return body
}

export async function checkHealth() {
  return request('/health')
}

/**
 * GET /api/v1/transactions/{reference}
 * -> { reference, customer_reference, amount, currency, status, payment_method, created_at }
 */
export async function getTransaction(reference) {
  return request(`/api/v1/transactions/${encodeURIComponent(reference)}`)
}

/**
 * GET /api/v1/customers/{reference}
 * -> { reference, name, phone, email, created_at }
 * phone/email are masked by the backend (no authentication yet -- see
 * docs/security.md) -- do not rely on them being the full value.
 */
export async function getCustomer(reference) {
  return request(`/api/v1/customers/${encodeURIComponent(reference)}`)
}

/**
 * POST /api/v1/support/cases
 * Required: customer_reference, category, description.
 * Optional: transaction_reference.
 * -> { reference, customer_reference, transaction_reference, category, description, status, created_at }
 */
export async function createSupportCase({
  customerReference,
  description,
  category = 'general',
  transactionReference,
}) {
  return request('/api/v1/support/cases', {
    method: 'POST',
    body: JSON.stringify({
      customer_reference: customerReference,
      category,
      description,
      transaction_reference: transactionReference || null,
    }),
  })
}

/**
 * GET /api/v1/support/cases/{reference}
 * -> same shape as createSupportCase's response.
 *
 * There is no case-resolution/auto-investigate endpoint on the backend --
 * a case's status (OPEN / IN_REVIEW / RESOLVED / CLOSED) only changes when
 * a human agent updates it. Use this to re-check current status, not to
 * trigger investigation.
 */
export async function getSupportCase(reference) {
  return request(`/api/v1/support/cases/${encodeURIComponent(reference)}`)
}

/**
 * POST /api/v1/disputes
 * -> { reference, support_case_reference, transaction_reference, status, reason, created_at }
 *
 * The backend independently verifies that the transaction belongs to the
 * customer (ApiError code CUSTOMER_TRANSACTION_MISMATCH if not) and that
 * the transaction is in a disputable state (INVALID_TRANSACTION_STATE /
 * DISPUTE_NOT_ELIGIBLE) -- see docs/decisions/005-dispute-eligibility-matrix.md.
 */
export async function createDispute(customerReference, transactionReference, reason) {
  return request('/api/v1/disputes', {
    method: 'POST',
    body: JSON.stringify({
      customer_reference: customerReference,
      transaction_reference: transactionReference,
      reason,
    }),
  })
}

/**
 * POST /api/v1/support/messages -- the AI-interprets / orchestration-
 * coordinates / backend-authorizes conversational endpoint (docs/ai.md,
 * docs/orchestration.md). Always resolves (HTTP 200) once the customer
 * reference itself is valid; check `outcome` to see what happened.
 */
export async function sendSupportMessage(customerReference, message) {
  return request('/api/v1/support/messages', {
    method: 'POST',
    body: JSON.stringify({ customer_reference: customerReference, message }),
  })
}

/**
 * There is no backend endpoint that answers "does this transaction belong
 * to this customer" as a standalone read -- GET /transactions/{reference}
 * already returns `customer_reference`, so ownership is checked client-side
 * by comparing it. See CustomerVerificationPage / DisputePaymentPage, and
 * the note in the frontend README on why this needed no backend change.
 */
export async function verifyCustomerOwnsTransaction(customerReference, transactionReference) {
  const [customer, transaction] = await Promise.all([
    getCustomer(customerReference),
    getTransaction(transactionReference),
  ])

  return {
    customer,
    transaction,
    verified: transaction.customer_reference === customer.reference,
  }
}
