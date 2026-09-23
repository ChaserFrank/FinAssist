"""Seed synthetic demo data for local development and demos.

Placeholder for the foundation PR. Once the domain schema and migrations
exist, this script will create reproducible synthetic records (e.g.
CUS-10001..., TXN-84721... with SUCCESS/FAILED/PENDING/REVERSED
scenarios) so the whole team can demo against identical data.

No real customer or financial data will ever be used here.
"""


def main() -> None:
    """Entry point for `python -m scripts.seed_demo_data` (not yet runnable)."""
    raise NotImplementedError(
        "Seed data will be implemented once the domain schema and "
        "migrations exist."
    )


if __name__ == "__main__":
    main()
