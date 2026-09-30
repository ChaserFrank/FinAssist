import { useState } from 'react'
import SupportInput from './components/SupportInput'
import CommonIssues from './components/CommonIssues'
import { sendSupportMessage } from './services/api'

const OUTCOME_LABELS = {
  needs_info: 'More information needed',
  not_found: 'Not found',
  status_reported: 'Payment status',
  case_status: 'Case status',
  dispute_created: 'Dispute opened',
  dispute_declined: 'Dispute not eligible',
}

export default function SupportPage({
  onCheckPayment,
  onPaymentReversed,
  onReportIssue,
  onVerifyPayment,
  onDisputePayment,
}) {
  const [customerReference, setCustomerReference] = useState('')
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Free-text messages go to POST /api/v1/support/messages -- the
  // AI-interprets / orchestration-coordinates / backend-authorizes flow
  // (docs/ai.md, docs/orchestration.md). The other Common Options cards
  // below route to dedicated pages that call specific endpoints directly.
  async function handleSubmit(event) {
    event.preventDefault()

    if (!message.trim()) {
      return
    }

    if (!customerReference.trim()) {
      setError('Enter your customer reference so we can look up your account.')
      return
    }

    setIsSubmitting(true)
    setError('')
    setResult(null)

    try {
      const response = await sendSupportMessage(customerReference.trim(), message.trim())
      setResult(response)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSelectIssue = (description) => {
    setMessage(description)
    setResult(null)
    setError('')
  }

  return (
    <div className="support-container">
      <div className="welcome-section">
        <p className="eyebrow">Support Center</p>

        <h1>How can we help you today?</h1>

        <p className="intro">Describe your issue below or choose a common option.</p>
      </div>

      <div className="customer-field">
        <label htmlFor="support-customer-reference">Your customer reference</label>

        <input
          id="support-customer-reference"
          type="text"
          value={customerReference}
          onChange={(event) => setCustomerReference(event.target.value)}
          placeholder="e.g. CUS-10021"
          disabled={isSubmitting}
        />
      </div>

      <SupportInput
        message={message}
        onMessageChange={setMessage}
        onSubmit={handleSubmit}
        disabled={isSubmitting}
      />

      {error && <p className="error-message">{error}</p>}

      {result && (
        <section className="payment-result">
          <div className="result-row">
            <span>{OUTCOME_LABELS[result.outcome] || result.outcome}</span>
          </div>

          <p>{result.reply}</p>

          {result.transaction && (
            <>
              <div className="result-row">
                <span>Payment reference</span>
                <strong>{result.transaction.reference}</strong>
              </div>

              <div className="result-row">
                <span>Status</span>
                <strong>{result.transaction.status}</strong>
              </div>
            </>
          )}

          {result.case_reference && (
            <div className="result-row">
              <span>Support case</span>
              <strong>{result.case_reference}</strong>
            </div>
          )}

          {result.dispute_reference && (
            <div className="result-row">
              <span>Dispute</span>
              <strong>{result.dispute_reference}</strong>
            </div>
          )}
        </section>
      )}

      <CommonIssues
        onSelectIssue={handleSelectIssue}
        onCheckPayment={onCheckPayment}
        onPaymentReversed={onPaymentReversed}
        onReportIssue={onReportIssue}
        onVerifyPayment={onVerifyPayment}
        onDisputePayment={onDisputePayment}
      />
    </div>
  )
}
