"""Test package.

Sets a harmless default so importing ``app`` never needs a real database
URL. Unit and API tests build their own in-memory SQLite engines and never
use this value to connect to anything. Integration tests use a *separate*
``TEST_DATABASE_URL`` (see tests/integration).
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
