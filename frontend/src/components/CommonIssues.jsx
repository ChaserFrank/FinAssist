export default function CommonIssues({
  onSelectIssue,
  onCheckPayment,
  onPaymentReversed,
  onReportIssue,
}) {
  const issues = [
    {
      id: '01',
      title: 'Check a payment',
      desc: 'Find out what happened to a payment.',
    },
    {
      id: '02',
      title: 'Payment reversed',
      desc: 'Understand why a payment was reversed.',
    },
    {
      id: '03',
      title: 'Report a payment issue',
      desc: 'Tell us about a problem with a transaction.',
    },
  ]

  return (
    <section className="suggestions">
      <p className="eyebrow">Quick Options</p>

      <h2>Common payment issues</h2>

      <p className="suggestion-subtitle">
        Choose an option to get started faster.
      </p>

      <div className="suggestion-grid">
        {issues.map((issue) => (
          <button
            key={issue.id}
            className="suggestion-card"
            type="button"
            onClick={() => {
              if (issue.id === '01') {
                onCheckPayment()
                return
              }

              if (issue.id === '02') {
                onPaymentReversed()
                return
              }

              if (issue.id === '03') {
                onReportIssue()
                return
              }

              onSelectIssue(issue.desc)
            }}
          >
            <strong>
              <span className="card-number">{issue.id}</span>
              {issue.title}
            </strong>

            <span>
              {issue.desc} <span className="arrow">→</span>
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
