import { useState } from 'react'
import SupportInput from './components/SupportInput'
import CommonIssues from './components/CommonIssues'

export default function SupportPage({
  onCheckPayment,
  onPaymentReversed,
  onReportIssue,
  onVerifyPayment,
  onDisputePayment,
}) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Submitting:', message)
  }

  const handleSelectIssue = (description) => {
    setMessage(description)
  }

  return (
    <div className="support-container">
      <div className="welcome-section">
        <p className="eyebrow">Support Center</p>

        <h1>How can we help you today?</h1>

        <p className="intro">
          Describe your issue below or choose a common option.
        </p>
      </div>

      <SupportInput
        message={message}
        onMessageChange={setMessage}
        onSubmit={handleSubmit}
      />

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