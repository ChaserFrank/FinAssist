import { useState } from 'react'
import { createSupportCase } from '../services/api'

function ReportPaymentIssuePage({ onBack }) {
  const [reference, setReference] = useState('')
  const [message, setMessage] = useState('')
  const [supportCase, setSupportCase] = useState(null)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    const trimmedReference = reference.trim()
    const trimmedMessage = message.trim()

    if (!trimmedReference) {
      setError('Enter a payment reference.')
      return
    }

    if (!trimmedMessage) {
      setError('Tell us what happened with the payment.')
      return
    }

    setIsSubmitting(true)
    setError('')

    try {
      const data = await createSupportCase(
        trimmedReference,
        trimmedMessage
      )

      setSupportCase(data)
    } catch (err) {
      setError(
        err.message || 'Something went wrong while submitting your report.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (supportCase) {
    return (
      <main className="page">
        <div className="page-header">
          <button type="button" className="back-button" onClick={onBack}>
            ← Back
          </button>

          <h1>Payment Issue Reported</h1>

          <p>Your payment issue has been sent to customer support.</p>
        </div>

        <section className="payment-result">
          <div className="result-row">
            <span>Case reference</span>
            <strong>{supportCase.reference}</strong>
          </div>

          <div className="result-row">
            <span>Payment reference</span>
            <strong>{supportCase.transaction_reference}</strong>
          </div>

          <div className="result-row">
            <span>Status</span>
            <strong>{supportCase.status}</strong>
          </div>

          <div className="support-success">
            <h2>Customer care has received your query</h2>

            <p>
              Our support team can use your case reference to investigate
              the payment and respond to your issue.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={onBack}
          >
            Return to Support Center
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

        <h1>Report a Payment Issue</h1>

        <p>
          Tell us about the payment problem and our support team can
          investigate it.
        </p>
      </div>

      <form className="support-form" onSubmit={handleSubmit}>
        <label htmlFor="issue-reference">
          Payment reference
        </label>

        <input
          id="issue-reference"
          type="text"
          value={reference}
          onChange={(event) => setReference(event.target.value)}
          placeholder="e.g. TXN-DEMO-001"
          disabled={isSubmitting}
        />

        <label htmlFor="issue-message">
          What happened?
        </label>

        <textarea
          id="issue-message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Describe the problem with your payment."
          rows="6"
          disabled={isSubmitting}
        />

        {error && <p className="error-message">{error}</p>}

        <button
          type="submit"
          className="primary-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting report...' : 'Submit payment issue'}
        </button>
      </form>
    </main>
  )
}

export default ReportPaymentIssuePage