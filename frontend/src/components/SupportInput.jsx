function SupportInput({ message, onMessageChange, onSubmit }) {
  return (
    <section className="support-card">
      <form onSubmit={onSubmit}>
        <label htmlFor="payment-message">
          Describe your payment issue
        </label>

        <textarea
          id="payment-message"
          value={message}
          onChange={(event) => onMessageChange(event.target.value)}
          placeholder="For example: I was charged, but my payment hasn't gone through."
          rows="5"
        />

        <button
          className="primary-button"
          type="submit"
          disabled={!message.trim()}
        >
          Get help
        </button>
      </form>
    </section>
  )
}

export default SupportInput