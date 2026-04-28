"""Mock customer profile data generator."""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any


def generate_customer_profile(policy_number: str) -> dict[str, Any]:
    """Generate fake customer profile data based on policy number.

    Args:
        policy_number: The policy number (e.g., "POL-2023-4567")

    Returns:
        Dictionary with customer profile data including membership_since
    """
    # Seed random with policy number for consistency
    random.seed(policy_number)

    # Generate random membership date between 1-10 years ago
    years_ago = random.randint(1, 10)
    days_offset = random.randint(0, 364)

    membership_date = datetime.now() - timedelta(days=years_ago * 365 + days_offset)

    return {
        "membership_since": membership_date.strftime("%Y-%m-%d"),
    }
