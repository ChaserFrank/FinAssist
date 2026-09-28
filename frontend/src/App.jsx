import { useState } from 'react'
import SupportPage from './SupportPage'
import PaymentLookupPage from './pages/PaymentLookupPage'
import PaymentReversedPage from './pages/PaymentReversedPage'
import ReportPaymentIssuePage from './pages/ReportPaymentIssuePage'
import CustomerVerificationPage from './pages/CustomerVerificationPage'
import DisputePaymentPage from './pages/DisputePaymentPage'

function App() {
  const [currentPage, setCurrentPage] = useState('support')

  if (currentPage === 'payment-lookup') {
    return (
      <PaymentLookupPage
        onBack={() => setCurrentPage('support')}
      />
    )
  }

  if (currentPage === 'payment-reversed') {
    return (
      <PaymentReversedPage
        onBack={() => setCurrentPage('support')}
      />
    )
  }

  if (currentPage === 'report-payment-issue') {
    return (
      <ReportPaymentIssuePage
        onBack={() => setCurrentPage('support')}
      />
    )
  }

  if (currentPage === 'customer-verification') {
    return (
      <CustomerVerificationPage
        onBack={() => setCurrentPage('support')}
      />
    )
  }

  if (currentPage === 'dispute-payment') {
    return (
      <DisputePaymentPage
        onBack={() => setCurrentPage('support')}
      />
    )
  }

  return (
    <div className="App">
      <SupportPage
        onCheckPayment={() => setCurrentPage('payment-lookup')}
        onPaymentReversed={() => setCurrentPage('payment-reversed')}
        onReportIssue={() => setCurrentPage('report-payment-issue')}
        onVerifyPayment={() =>
          setCurrentPage('customer-verification')
        }
        onDisputePayment={() =>
          setCurrentPage('dispute-payment')
        }
      />
    </div>
  )
}

export default App