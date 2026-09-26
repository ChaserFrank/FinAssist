import { useState } from 'react'
import SupportInput from '../components/SupportInput'

function SupportPage() {
  const [message, setMessage] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!message.trim()) {
      return
    }

    console.log('Support request:', message)
  }

  return (
    <div className="support-page">
      <header className="topbar">
        <div className="brand">FinAssist</div>
        <button className="support-link">Support</button>
      </header>

      <main className="support-container">
        <section className="welcome-section">
          <p className="eyebrow">Payment support</p>

          <h1>How can we help with your payment?</h1>

          <p className="intro">
            Tell us what happened and FinAssist will help you find the next
            step.
          </p>
        </section>

        <SupportInput
          message={message}
          onMessageChange={setMessage}
          onSubmit={handleSubmit}
        />

        <section className="suggestions">
          <h2>Common payment issues</h2>

          <div className="suggestion-grid">
            <button
              className="suggestion-card"
              type="button"
              onClick={() =>
                setMessage('I want to check the status of a payment.')
              }
            >
              <strong>Check a payment</strong>
              <span>Find out what happened to a payment.</span>
            </button>

            <button
              className="suggestion-card"
              type="button"
              onClick={() => setMessage('My payment was reversed.')}
            >
              <strong>Payment reversed</strong>
              <span>Understand why a payment was reversed.</span>
            </button>

            <button
              className="suggestion-card"
              type="button"
              onClick={() =>
                setMessage('I want to report a payment issue.')
              }
            >
              <strong>Report a payment issue</strong>
              <span>Tell us about a problem with a transaction.</span>
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default SupportPage