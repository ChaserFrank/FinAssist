import { useState } from 'react'
import { ApiError, createDispute, verifyCustomerOwnsTransaction } from '../services/api'

const DECLINE_MESSAGES = {
  INVALID_TRANSACTION_STATE:
    'This payment is not eligible for a dispute in its current state (pending or already reversed).',
  DISPUTE_NOT_ELIGIBLE: 'This payment already has an open or previously-resolved dispute.',
}

function DisputePaymentPage({ onBack }) {
  const [customerReference, setCustomerReference] = useState('')
  const [transactionReference, setTransactionReference] = useState('')
  const [reason, setReason] = useState('')
  const [verification, setVerification] = useState(null)
  const [dispute, setDispute] = useState(null)
  const [error, setError] = useState('')
  const [isChecking, setIsChecking] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  async function handleVerify(event) {
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
    setVerification(null)
    setError('')

    try {
      const data = await verifyCustomerOwnsTransaction(
        trimmedCustomerReference,
        trimmedTransactionReference
      )
      setVerification(data)

      if (!data.verified) {
        setError('This payment does not belong to the customer provided.')
      }
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

  async function handleCreateDispute(event) {
    event.preventDefault()

    const trimmedReason = reason.trim()

    if (!trimmedReason) {
      setError('Enter a reason for the dispute.')
      return
    }

    setIsCreating(true)
    setError('')

    try {
      // The backend independently re-verifies ownership and eligibility here
      // (docs/decisions/005-dispute-eligibility-matrix.md) -- the client-side
      // check above is a UX convenience, not the security boundary.
      const disputeData = await createDispute(
        customerReference.trim(),
        transactionReference.trim(),
        trimmedReason
      )
      setDispute(disputeData)
    } catch (err) {
      if (err instanceof ApiError && DECLINE_MESSAGES[err.code]) {
        setError(DECLINE_MESSAGES[err.code])
      } else if (err instanceof ApiError && err.code === 'CUSTOMER_TRANSACTION_MISMATCH') {
        setError('This payment does not belong to the customer provided.')
      } else {
        setError(err.message || 'Something went wrong while creating the dispute.')
      }
    } finally {
      setIsCreating(false)
    }
  }

  function handleStartOver() {
    setCustomerReference('')
    setTransactionReference('')
    setReason('')
    setVerification(null)
    setDispute(null)
    setError('')
  }

  return (
    <main className="page">
      <div className="page-header">
        <button type="button" className="back-button" onClick={onBack}>
          ← Back
        </button>

        <h1>Dispute a Payment</h1>

        <p>Verify the payment belongs to the customer before creating a dispute.</p>
      </div>

      {!verification && !dispute && (
        <form className="support-form" onSubmit={handleVerify}>
          <label htmlFor="dispute-customer-reference">Customer reference</label>

          <input
            id="dispute-customer-reference"
            type="text"
            value={customerReference}
            onChange={(event) => setCustomerReference(event.target.value)}
            placeholder="e.g. CUS-10021"
            disabled={isChecking}
          />

          <label htmlFor="dispute-transaction-reference">Payment reference</label>

          <input
            id="dispute-transaction-reference"
            type="text"
            value={transactionReference}
            onChange={(event) => setTransactionReference(event.target.value)}
            placeholder="e.g. TXN-84722"
            disabled={isChecking}
          />

          {error && <p className="error-message">{error}</p>}

          <button type="submit" className="primary-button" disabled={isChecking}>
            {isChecking ? 'Verifying payment...' : 'Verify payment'}
          </button>
        </form>
      )}

      {verification && !dispute && (
        <section className="payment-result">
          <div className="result-row">
            <span>Customer</span>
            <strong>{verification.customer.name}</strong>
          </div>

          <div className="result-row">
            <span>Customer reference</span>
            <strong>{verification.customer.reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment reference</span>
            <strong>{verification.transaction.reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment status</span>
            <strong>{verification.transaction.status}</strong>
          </div>

          <div className="result-row">
            <span>Ownership</span>
            <strong>{verification.verified ? 'VERIFIED' : 'NOT VERIFIED'}</strong>
          </div>

          {verification.verified && (
            <form className="support-form" onSubmit={handleCreateDispute}>
              <label htmlFor="dispute-reason">Reason for dispute</label>

              <textarea
                id="dispute-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Explain what happened with the payment."
                rows="5"
                disabled={isCreating}
              />

              {error && <p className="error-message">{error}</p>}

              <button type="submit" className="primary-button" disabled={isCreating}>
                {isCreating ? 'Creating dispute...' : 'Create dispute'}
              </button>
            </form>
          )}

          {!verification.verified && (
            <>
              {error && <p className="error-message">{error}</p>}

              <button type="button" className="secondary-button" onClick={handleStartOver}>
                Try another payment
              </button>
            </>
          )}
        </section>
      )}

      {dispute && (
        <section className="payment-result">
          <div className="support-success">
            <h2>Dispute created</h2>

            <p>Your payment dispute has been recorded and a support case has been opened.</p>
          </div>

          <div className="result-row">
            <span>Dispute reference</span>
            <strong>{dispute.reference}</strong>
          </div>

          <div className="result-row">
            <span>Support case</span>
            <strong>{dispute.support_case_reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment reference</span>
            <strong>{dispute.transaction_reference}</strong>
          </div>

          <div className="result-row">
            <span>Reason</span>
            <strong>{dispute.reason}</strong>
          </div>

          <div className="result-row">
            <span>Status</span>
            <strong>{dispute.status}</strong>
          </div>

          <button type="button" className="secondary-button" onClick={handleStartOver}>
            Dispute another payment
          </button>
        </section>
      )}
    </main>
  )
}

export default DisputePaymentPage
