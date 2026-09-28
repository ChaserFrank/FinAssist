import { useState } from 'react'
import { getCustomer, verifyCustomerTransaction } from '../services/api'

function CustomerVerificationPage({ onBack }) {
  const [customerReference, setCustomerReference] = useState('')
  const [transactionReference, setTransactionReference] = useState('')
  const [verification, setVerification] = useState(null)
  const [customer, setCustomer] = useState(null)
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
    setVerification(null)
    setCustomer(null)
    setError('')

    try {
      const [customerData, verificationData] = await Promise.all([
        getCustomer(trimmedCustomerReference),
        verifyCustomerTransaction(
          trimmedCustomerReference,
          trimmedTransactionReference
        ),
      ])

      setCustomer(customerData)
      setVerification(verificationData)
    } catch (err) {
      setError(
        err.message ||
          'Something went wrong while verifying the payment.'
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

        <h1>Verify a Payment</h1>

        <p>
          Confirm that a payment belongs to the customer account.
        </p>
      </div>

      {!verification && (
        <form className="support-form" onSubmit={handleSubmit}>
          <label htmlFor="customer-reference">
            Customer reference
          </label>

          <input
            id="customer-reference"
            type="text"
            value={customerReference}
            onChange={(event) =>
              setCustomerReference(event.target.value)
            }
            placeholder="e.g. CUS-DEMO-001"
            disabled={isChecking}
          />

          <label htmlFor="verification-transaction">
            Payment reference
          </label>

          <input
            id="verification-transaction"
            type="text"
            value={transactionReference}
            onChange={(event) =>
              setTransactionReference(event.target.value)
            }
            placeholder="e.g. TXN-DEMO-001"
            disabled={isChecking}
          />

          {error && <p className="error-message">{error}</p>}

          <button
            type="submit"
            className="primary-button"
            disabled={isChecking}
          >
            {isChecking ? 'Verifying payment...' : 'Verify payment'}
          </button>
        </form>
      )}

      {verification && (
        <section className="payment-result">
          <div className="result-row">
            <span>Customer</span>
            <strong>{customer?.name}</strong>
          </div>

          <div className="result-row">
            <span>Customer reference</span>
            <strong>{verification.customer_reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment reference</span>
            <strong>{verification.transaction_reference}</strong>
          </div>

          <div className="result-row">
            <span>Verification</span>
            <strong>
              {verification.verified ? 'VERIFIED' : 'NOT VERIFIED'}
            </strong>
          </div>

          <div className="support-success">
            <h2>
              {verification.verified
                ? 'Payment verified'
                : 'Payment not verified'}
            </h2>

            <p>
              {verification.verified
                ? 'This payment is linked to the customer account provided.'
                : 'This payment is not linked to the customer account provided.'}
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setCustomerReference('')
              setTransactionReference('')
              setVerification(null)
              setCustomer(null)
              setError('')
            }}
          >
            Verify another payment
          </button>
        </section>
      )}
    </main>
  )
}

export default CustomerVerificationPage