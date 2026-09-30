function SupportInput({
  message,
  onMessageChange,
  onSubmit,
  disabled = false,
}) {
  return (
    <div className="support-card">
      <form className="support-form" onSubmit={onSubmit}>
        <div className="input-header">
          <div>
            <label htmlFor="payment-issue" className="support-label">
              Describe your payment issue
            </label>

            <p className="input-help">
              Include any details that may help us understand what happened.
            </p>
          </div>
        </div>

        <textarea
          id="payment-issue"
          className="support-textarea"
          value={message}
          onChange={(event) => onMessageChange(event.target.value)}
          placeholder="For example: My payment was deducted but the recipient did not receive it."
          rows={5}
          disabled={disabled}
        />

        <div className="form-footer">
          <span className="input-note">
            Do not include your PIN or password.
          </span>

          <button
            type="submit"
            className="primary-button"
            disabled={disabled || !message.trim()}
          >
            {disabled ? 'Sending…' : 'Get help'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default SupportInput;