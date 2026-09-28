import { useState } from 'react'
import SupportInput from '../components/SupportInput'
import PaymentLookupPage from './PaymentLookupPage'

const commonIssues = [
  {
    icon: '01',
    title: 'Check a payment',
    description: 'Find out what happened to a payment.',
    message: 'I want to check the status of my payment.',
  },
  {
    icon: '02',
    title: 'Payment reversed',
    description: 'Understand why a payment was reversed.',
    message: 'My payment was reversed.',
  },
  {
    icon: '03',
    title: 'Report a payment issue',
    description: 'Tell us about a problem with a transaction.',
    message: 'I want to report a problem with a payment.',
  },
]

function SupportPage() {
  const [message, setMessage] = useState('')
  const [submittedMessage, setSubmittedMessage] = useState('')
  const [showPaymentLookup, setShowPaymentLookup] = useState(false)

  function handleSubmit(event) {
    event.preventDefault()

    if (!message.trim()) {
      return
    }

    setSubmittedMessage(message.trim())
  }

  function handleIssueClick(issueMessage) {
    setMessage(issueMessage)
    setSubmittedMessage('')
  }

  if (showPaymentLookup) {
    return (
      <PaymentLookupPage
        onBack={() => setShowPaymentLookup(false)}
      />
    )
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Payment support</p>

        <h1>How can we help with your payment?</h1>

        <p className="hero-description">
          Tell us what happened and FinAssist will help you find the next step.
        </p>
      </section>

      <section className="support-card">
        <SupportInput
          message={message}
          onMessageChange={setMessage}
          onSubmit={handleSubmit}
        />

        {submittedMessage && (
          <div className="status status-success">
            <strong>Thanks. We received your message.</strong>

            <p>
              FinAssist will use the information you provided to help identify
              the next step.
            </p>
          </div>
        )}
      </section>

      <section className="common-issues">
        <div className="section-heading">
          <p className="section-eyebrow">Quick options</p>

          <h2>Common payment issues</h2>

          <p>
            Choose an option to get started faster.
          </p>
        </div>

        <div className="issue-grid">
          {commonIssues.map((issue) => (
            <button
              key={issue.title}
              type="button"
              className="issue-card"
              onClick={() => {
                if (issue.title === 'Check a payment') {
                  setShowPaymentLookup(true)
                  return
                }

                handleIssueClick(issue.message)
              }}
            >
              <span className="issue-icon">
                {issue.icon}
              </span>

              <span className="issue-content">
                <span className="issue-title">
                  {issue.title}
                </span>

                <span className="issue-description">
                  {issue.description}
                </span>
              </span>

              <span className="issue-arrow">
                →
              </span>
            </button>
          ))}
        </div>
      </section>
    </main>
  )
}

export default SupportPage