import { useState } from 'react'
import { ApiError, verifyCustomerOwnsTransaction } from '../services/api'

// There is no dedicated "verify" endpoint on the backend: GET
// /api/v1/transactions/{reference} already returns customer_reference, so
// ownership is checked here by comparing it against the customer looked up
// via GET /api/v1/customers/{reference}. See services/api.js.
function CustomerVerificationPage({ onBack }) {
  const [customerReference, setCustomerReference] = useState('')
  const [transactionReference, setTransactionReference] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [isChecking, setIsChecking] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    const trimmedCustomerReference = customerReference.trim()
    const trimmedTransactionReference = transactionReference.trim()

    if (!trimmedCustomerReference) {
      setError('Enter a customer reference.')
      return
    }

    if (!trimmedTransactionReference) {
      setError('Enter a payment reference.')
      return
    }

    setIsChecking(true)
    setResult(null)
    setError('')

    try {
      const data = await verifyCustomerOwnsTransaction(
        trimmedCustomerReference,
        trimmedTransactionReference
      )
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'CUSTOMER_NOT_FOUND') {
        setError(`We couldn't find a customer with reference "${trimmedCustomerReference}".`)
      } else if (err instanceof ApiError && err.code === 'TRANSACTION_NOT_FOUND') {
        setError(`We couldn't find a payment with reference "${trimmedTransactionReference}".`)
      } else {
        setError(err.message || 'Something went wrong while verifying the payment.')
      }
    } finally {
      setIsChecking(false)
    }
  }

  function handleReset() {
    setCustomerReference('')
    setTransactionReference('')
    setResult(null)
    setError('')
  }

  return (
    <main className="page">
      <div className="page-header">
        <button type="button" className="back-button" onClick={onBack}>
          ← Back
        </button>

        <h1>Verify a Payment</h1>

        <p>Confirm that a payment belongs to the customer account.</p>
      </div>

      {!result && (
        <form className="support-form" onSubmit={handleSubmit}>
          <label htmlFor="customer-reference">Customer reference</label>

          <input
            id="customer-reference"
            type="text"
            value={customerReference}
            onChange={(event) => setCustomerReference(event.target.value)}
            placeholder="e.g. CUS-10021"
            disabled={isChecking}
          />

          <label htmlFor="verification-transaction">Payment reference</label>

          <input
            id="verification-transaction"
            type="text"
            value={transactionReference}
            onChange={(event) => setTransactionReference(event.target.value)}
            placeholder="e.g. TXN-84721"
            disabled={isChecking}
          />

          {error && <p className="error-message">{error}</p>}

          <button type="submit" className="primary-button" disabled={isChecking}>
            {isChecking ? 'Verifying payment...' : 'Verify payment'}
          </button>
        </form>
      )}

      {result && (
        <section className="payment-result">
          <div className="result-row">
            <span>Customer</span>
            <strong>{result.customer.name}</strong>
          </div>

          <div className="result-row">
            <span>Customer reference</span>
            <strong>{result.customer.reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment reference</span>
            <strong>{result.transaction.reference}</strong>
          </div>

          <div className="result-row">
            <span>Verification</span>
            <strong>{result.verified ? 'VERIFIED' : 'NOT VERIFIED'}</strong>
          </div>

          <div className="support-success">
            <h2>{result.verified ? 'Payment verified' : 'Payment not verified'}</h2>

            <p>
              {result.verified
                ? 'This payment is linked to the customer account provided.'
                : 'This payment is not linked to the customer account provided.'}
            </p>
          </div>

          <button type="button" className="secondary-button" onClick={handleReset}>
            Verify another payment
          </button>
        </section>
      )}
    </main>
  )
}

export default CustomerVerificationPage
