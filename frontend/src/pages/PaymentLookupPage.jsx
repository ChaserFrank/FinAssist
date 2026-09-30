import { useState } from 'react'
import { ApiError, createSupportCase, getSupportCase, getTransaction } from '../services/api'

function PaymentLookupPage({ onBack }) {
  const [reference, setReference] = useState('')
  const [isChecking, setIsChecking] = useState(false)
  const [payment, setPayment] = useState(null)
  const [error, setError] = useState('')

  const [showSupportForm, setShowSupportForm] = useState(false)
  const [customerReference, setCustomerReference] = useState('')
  const [supportMessage, setSupportMessage] = useState('')
  const [isSubmittingSupport, setIsSubmittingSupport] = useState(false)
  const [supportCase, setSupportCase] = useState(null)
  const [supportError, setSupportError] = useState('')
  const [isRefreshingCase, setIsRefreshingCase] = useState(false)

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
    setShowSupportForm(false)
    setSupportCase(null)

    try {
      const data = await getTransaction(trimmedReference)
      setPayment(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'TRANSACTION_NOT_FOUND') {
        setError('We could not find a payment with that reference.')
      } else {
        setError(err.message || 'Something went wrong while checking the payment.')
      }
    } finally {
      setIsChecking(false)
    }
  }

  async function handleSupportSubmit(event) {
    event.preventDefault()

    const trimmedCustomerReference = customerReference.trim()
    const trimmedMessage = supportMessage.trim()

    if (!trimmedCustomerReference) {
      setSupportError('Enter your customer reference so we can open the case under your account.')
      return
    }

    if (!trimmedMessage) {
      setSupportError('Tell us what happened before submitting your request.')
      return
    }

    setIsSubmittingSupport(true)
    setSupportError('')

    try {
      const data = await createSupportCase({
        customerReference: trimmedCustomerReference,
        category: 'payment_inquiry',
        description: trimmedMessage,
        transactionReference: payment.reference,
      })
      setSupportCase(data)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'CUSTOMER_NOT_FOUND') {
        setSupportError(`We couldn't find a customer with reference "${trimmedCustomerReference}".`)
      } else if (err instanceof ApiError && err.code === 'CUSTOMER_TRANSACTION_MISMATCH') {
        setSupportError('This payment does not belong to the customer reference you entered.')
      } else {
        setSupportError(err.message || 'Something went wrong while submitting your request.')
      }
    } finally {
      setIsSubmittingSupport(false)
    }
  }

  // The backend has no case-resolution/auto-investigate endpoint -- a case's
  // status only changes when a human agent updates it (docs/api.md). This
  // re-fetches the case's current status rather than pretending to trigger
  // an investigation.
  async function handleRefreshCaseStatus() {
    if (!supportCase?.reference) return

    setIsRefreshingCase(true)
    setSupportError('')

    try {
      const data = await getSupportCase(supportCase.reference)
      setSupportCase(data)
    } catch (err) {
      setSupportError(err.message || 'Something went wrong while checking your case.')
    } finally {
      setIsRefreshingCase(false)
    }
  }

  function handleCheckAnother() {
    setReference('')
    setPayment(null)
    setError('')
    setShowSupportForm(false)
    setCustomerReference('')
    setSupportMessage('')
    setSupportCase(null)
    setSupportError('')
  }

  if (payment) {
    return (
      <main className="page">
        <div className="page-header">
          <button type="button" className="back-button" onClick={onBack}>
            ← Back
          </button>

          <h1>Payment Details</h1>
          <p>Here is what we found for this payment.</p>
        </div>

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

          {!supportCase && !showSupportForm && (
            <button
              type="button"
              className="primary-button"
              onClick={() => setShowSupportForm(true)}
            >
              Contact Support
            </button>
          )}

          {showSupportForm && !supportCase && (
            <form className="support-form" onSubmit={handleSupportSubmit}>
              <label htmlFor="support-customer-reference">Your customer reference</label>

              <input
                id="support-customer-reference"
                type="text"
                value={customerReference}
                onChange={(event) => setCustomerReference(event.target.value)}
                placeholder="e.g. CUS-10021"
                disabled={isSubmittingSupport}
              />

              <label htmlFor="support-message">Tell us what happened</label>

              <textarea
                id="support-message"
                value={supportMessage}
                onChange={(event) => setSupportMessage(event.target.value)}
                placeholder="For example: My payment has been pending for several hours."
                rows="5"
                disabled={isSubmittingSupport}
              />

              {supportError && <p className="error-message">{supportError}</p>}

              <button type="submit" className="primary-button" disabled={isSubmittingSupport}>
                {isSubmittingSupport ? 'Submitting request...' : 'Submit support request'}
              </button>
            </form>
          )}

          {supportCase && (
            <div className="support-success">
              <h2>Support request received</h2>

              <p>Your request has been submitted for review.</p>

              <div className="result-row">
                <span>Case reference</span>
                <strong>{supportCase.reference}</strong>
              </div>

              <div className="result-row">
                <span>Status</span>
                <strong>{supportCase.status}</strong>
              </div>

              <p>Our support team can use this case reference to investigate your payment.</p>

              {supportError && <p className="error-message">{supportError}</p>}

              <button
                type="button"
                className="primary-button"
                onClick={handleRefreshCaseStatus}
                disabled={isRefreshingCase}
              >
                {isRefreshingCase ? 'Checking...' : 'Refresh case status'}
              </button>
            </div>
          )}

          <button type="button" className="secondary-button" onClick={handleCheckAnother}>
            Check another payment
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="page">
      <div className="page-header">
        <button type="button" className="back-button" onClick={onBack}>
          ← Back
        </button>

        <h1>Check a Payment</h1>
        <p>Enter your payment reference to see what happened.</p>
      </div>

      <form className="support-form" onSubmit={handleSubmit}>
        <label htmlFor="payment-reference">Payment reference</label>

        <input
          id="payment-reference"
          type="text"
          value={reference}
          onChange={(event) => setReference(event.target.value)}
          placeholder="e.g. TXN-84721"
          disabled={isChecking}
        />

        {error && <p className="error-message">{error}</p>}

        <button type="submit" className="primary-button" disabled={isChecking}>
          {isChecking ? 'Checking payment...' : 'Check payment'}
        </button>
      </form>
    </main>
  )
}

export default PaymentLookupPage
