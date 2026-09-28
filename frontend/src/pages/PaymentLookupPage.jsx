import { useState } from 'react'

const API_BASE_URL = 'http://127.0.0.1:8000'

function PaymentLookupPage({ onBack }) {
  const [reference, setReference] = useState('')
  const [isChecking, setIsChecking] = useState(false)
  const [payment, setPayment] = useState(null)
  const [error, setError] = useState('')
  const [showSupportForm, setShowSupportForm] = useState(false)
  const [supportMessage, setSupportMessage] = useState('')
  const [isSubmittingSupport, setIsSubmittingSupport] = useState(false)
  const [supportCase, setSupportCase] = useState(null)
  const [supportError, setSupportError] = useState('')
  const [isCheckingCase, setIsCheckingCase] = useState(false)

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
      const response = await fetch(
        `${API_BASE_URL}/api/v1/transactions/${encodeURIComponent(trimmedReference)}`
      )

      if (response.status === 404) {
        throw new Error('We could not find a payment with that reference.')
      }

      if (!response.ok) {
        throw new Error('We could not check the payment right now.')
      }

      const data = await response.json()
      setPayment(data)
    } catch (err) {
      setError(err.message || 'Something went wrong while checking the payment.')
    } finally {
      setIsChecking(false)
    }
  }

  async function handleSupportSubmit(event) {
    event.preventDefault()

    const trimmedMessage = supportMessage.trim()

    if (!trimmedMessage) {
      setSupportError('Tell us what happened before submitting your request.')
      return
    }

    setIsSubmittingSupport(true)
    setSupportError('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/support/cases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction_reference: payment.reference,
          message: trimmedMessage,
        }),
      })

      if (!response.ok) {
        throw new Error('We could not submit your support request.')
      }

      const data = await response.json()
      setSupportCase(data)
    } catch (err) {
      setSupportError(
        err.message || 'Something went wrong while submitting your request.'
      )
    } finally {
      setIsSubmittingSupport(false)
    }
  }

  async function handleCheckCaseStatus() {
    if (!supportCase?.reference) return

    setIsCheckingCase(true)
    setSupportError('')

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/support/cases/${encodeURIComponent(
          supportCase.reference
        )}/investigate`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error('We could not retrieve your support case.')
      }

      const data = await response.json()
      setSupportCase(data)
    } catch (err) {
      setSupportError(
        err.message || 'Something went wrong while checking your case.'
      )
    } finally {
      setIsCheckingCase(false)
    }
  }

  function handleCheckAnother() {
    setReference('')
    setPayment(null)
    setError('')
    setShowSupportForm(false)
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

          <div className="result-row">
            <span>Description</span>
            <strong>{payment.description}</strong>
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
              <label htmlFor="support-message">
                Tell us what happened
              </label>

              <textarea
                id="support-message"
                value={supportMessage}
                onChange={(event) => setSupportMessage(event.target.value)}
                placeholder="For example: My payment has been pending for several hours."
                rows="5"
                disabled={isSubmittingSupport}
              />

              {supportError && (
                <p className="error-message">{supportError}</p>
              )}

              <button
                type="submit"
                className="primary-button"
                disabled={isSubmittingSupport}
              >
                {isSubmittingSupport
                  ? 'Submitting request...'
                  : 'Submit support request'}
              </button>
            </form>
          )}

          {supportCase && (
            <div className="support-success">
              {supportCase.status === 'RESOLVED' ? (
                <>
                  <h2>Investigation complete</h2>

                  <p>
                    Our support team has checked your payment and provided a
                    response.
                  </p>

                  <div className="result-row">
                    <span>Case reference</span>
                    <strong>{supportCase.reference}</strong>
                  </div>

                  <div className="result-row">
                    <span>Status</span>
                    <strong>{supportCase.status}</strong>
                  </div>

                  <div className="support-response">
                    <span>Support response</span>
                    <p>{supportCase.response}</p>
                  </div>
                </>
              ) : (
                <>
                  <h2>Support request received</h2>

                  <p>
                    Your request has been submitted for review.
                  </p>

                  <div className="result-row">
                    <span>Case reference</span>
                    <strong>{supportCase.reference}</strong>
                  </div>

                  <div className="result-row">
                    <span>Status</span>
                    <strong>{supportCase.status}</strong>
                  </div>

                  <p>
                    Our support team can use this case reference to investigate
                    your payment.
                  </p>

                  {supportError && (
                    <p className="error-message">{supportError}</p>
                  )}

                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleCheckCaseStatus}
                    disabled={isCheckingCase}
                  >
                    {isCheckingCase
                      ? 'Checking case...'
                      : 'Check investigation status'}
                  </button>
                </>
              )}
            </div>
          )}

          <button
            type="button"
            className="secondary-button"
            onClick={handleCheckAnother}
          >
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
        <label htmlFor="payment-reference">
          Payment reference
        </label>

        <input
          id="payment-reference"
          type="text"
          value={reference}
          onChange={(event) => setReference(event.target.value)}
          placeholder="e.g. TXN-DEMO-001"
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
