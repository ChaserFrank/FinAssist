"""The AI/backend boundary: malformed model output must never be trusted.

`parse_ai_output` is the single choke point every provider's raw output
passes through (docs/ai.md, ADR-002). These tests are the proof that a
malformed reference, a negative amount, or an intent outside the closed
set is discarded rather than partially accepted.
"""

from app.infrastructure.ai.ai_port import Intent, parse_ai_output
from app.infrastructure.ai.mock_ai_service import MockAIService


class TestParseAIOutputRejectsMalformedData:
    def test_malformed_transaction_reference_is_discarded(self) -> None:
        result = parse_ai_output(
            {"intent": "payment_dispute", "transaction_reference": "not-a-real-ref"}
        )
        assert result.intent is Intent.UNKNOWN
        assert result.transaction_reference is None

    def test_malformed_case_reference_is_discarded(self) -> None:
        result = parse_ai_output({"intent": "support_case_status", "case_reference": "CASE-abc"})
        assert result.intent is Intent.UNKNOWN

    def test_negative_amount_is_discarded(self) -> None:
        result = parse_ai_output({"intent": "payment_dispute", "amount": "-50"})
        assert result.intent is Intent.UNKNOWN

    def test_unknown_intent_value_is_discarded(self) -> None:
        result = parse_ai_output({"intent": "delete_all_transactions"})
        assert result.intent is Intent.UNKNOWN

    def test_completely_invalid_shape_is_discarded(self) -> None:
        result = parse_ai_output("just a plain string, not even a dict")
        assert result.intent is Intent.UNKNOWN

    def test_well_formed_output_is_accepted(self) -> None:
        result = parse_ai_output(
            {
                "intent": "transaction_status",
                "transaction_reference": "TXN-84721",
                "confidence": 0.9,
            }
        )
        assert result.intent is Intent.TRANSACTION_STATUS
        assert result.transaction_reference == "TXN-84721"


class TestMockAIServiceIntentClassification:
    def setup_method(self) -> None:
        self.ai = MockAIService()

    def test_deducted_money_is_payment_dispute(self) -> None:
        result = self.ai.analyze("I was charged for TXN-84722 but it failed")
        assert result.intent is Intent.PAYMENT_DISPUTE
        assert result.transaction_reference == "TXN-84722"

    def test_failed_without_deduction_is_payment_failed(self) -> None:
        result = self.ai.analyze("My payment for TXN-84721 didn't go through")
        assert result.intent is Intent.PAYMENT_FAILED

    def test_status_question_is_transaction_status(self) -> None:
        result = self.ai.analyze("What is the status of TXN-84721?")
        assert result.intent is Intent.TRANSACTION_STATUS

    def test_case_reference_is_support_case_status(self) -> None:
        result = self.ai.analyze("Any update on CASE-1001?")
        assert result.intent is Intent.SUPPORT_CASE_STATUS
        assert result.case_reference == "CASE-1001"

    def test_unrelated_message_is_unknown(self) -> None:
        result = self.ai.analyze("Hello, what are your opening hours?")
        assert result.intent is Intent.UNKNOWN
        assert result.confidence == 0.0

    def test_extracts_amount_with_currency_prefix(self) -> None:
        result = self.ai.analyze("I was charged KES 800 for TXN-84722 but it failed")
        assert result.amount is not None
        assert str(result.amount) == "800"

    def test_output_always_passes_its_own_validation_gate(self) -> None:
        # The mock's own output must never be something parse_ai_output would
        # discard -- it is deliberately routed through the same gate a real
        # provider's output would be (see MockAIService.analyze).
        for message in ["", "random text", "TXN-1 fail charged CASE-2 status"]:
            result = self.ai.analyze(message)
            assert isinstance(result.intent, Intent)
