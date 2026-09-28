const API_BASE_URL = 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(
      data?.detail || 'The request could not be completed.'
    )
  }

  return data
}

export async function checkHealth() {
  return request('/health')
}

export async function getTransaction(reference) {
  return request(
    `/api/v1/transactions/${encodeURIComponent(reference)}`
  )
}

export async function createSupportCase(
  transactionReference,
  message
) {
  return request('/api/v1/support/cases', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      transaction_reference: transactionReference,
      message,
    }),
  })
}

export async function investigateSupportCase(reference) {
  return request(
    `/api/v1/support/cases/${encodeURIComponent(reference)}/investigate`,
    {
      method: 'POST',
    }
  )
}

export async function getCustomer(reference) {
  return request(
    `/api/v1/customers/${encodeURIComponent(reference)}`
  )
}

export async function verifyCustomerTransaction(
  customerReference,
  transactionReference
) {
  return request(
    `/api/v1/customers/${encodeURIComponent(
      customerReference
    )}/transactions/${encodeURIComponent(
      transactionReference
    )}/verify`
  )
}

export async function createDispute(
  customerReference,
  transactionReference,
  reason
) {
  return request('/api/v1/disputes', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_reference: customerReference,
      transaction_reference: transactionReference,
      reason,
    }),
  })
}