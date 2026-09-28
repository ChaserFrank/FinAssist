import { useState } from 'react'
import { getTransaction } from '../services/api'

function PaymentReversedPage({ onBack }) {
  const [reference, setReference] = useState('')
  const [payment, setPayment] = useState(null)
  const [error, setError] = useState('')
  const [isChecking, setIsChecking] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    const trimmedReference = reference.trim()

    if (!trimmedReference) {
      setError('Enter a payment reference.')
      return
    }

    setIsChecking(true)
    setPayment(null)
    setError('')

    try {
      const data = await getTransaction(trimmedReference)
      setPayment(data)
    } catch (err) {
      setError(
        err.message || 'Something went wrong while checking the payment.'
      )
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <main className="page">
      <div className="page-header">
        <button type="button" className="back-button" onClick={onBack}>
          ← Back
        </button>

        <h1>Payment Reversed</h1>

        <p>
          Enter your payment reference to understand what happened.
        </p>
      </div>

      {!payment && (
        <form className="support-form" onSubmit={handleSubmit}>
          <label htmlFor="reversed-reference">
            Payment reference
          </label>

          <input
            id="reversed-reference"
            type="text"
            value={reference}
            onChange={(event) => setReference(event.target.value)}
            placeholder="e.g. TXN-DEMO-004"
            disabled={isChecking}
          />

          {error && <p className="error-message">{error}</p>}

          <button
            type="submit"
            className="primary-button"
            disabled={isChecking}
          >
            {isChecking ? 'Checking payment...' : 'Check payment'}
          </button>
        </form>
      )}

      {payment && (
        <section className="payment-result">
          <div className="result-row">
            <span>Reference</span>
            <strong>{payment.reference}</strong>
          </div>

          <div className="result-row">
            <span>Amount</span>
            <strong>
              {payment.currency} {payment.amount}
            </strong>
          </div>

          <div className="result-row">
            <span>Status</span>
            <strong>{payment.status}</strong>
          </div>

          <div className="result-row">
            <span>Payment method</span>
            <strong>{payment.payment_method}</strong>
          </div>

          <div className="result-row">
            <span>Description</span>
            <strong>{payment.description}</strong>
          </div>

          {payment.status === 'REVERSED' ? (
            <div className="support-success">
              <h2>Payment reversed</h2>

              <p>
                This payment is recorded as reversed in the payment system.
                If you need further help, you can report the issue to support.
              </p>
            </div>
          ) : (
            <div className="support-success">
              <h2>Payment status found</h2>

              <p>
                This payment is currently recorded as {payment.status}.
                It is not marked as reversed.
              </p>
            </div>
          )}

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setReference('')
              setPayment(null)
              setError('')
            }}
          >
            Check another payment
          </button>
        </section>
      )}
    </main>
  )
}

export default PaymentReversedPage