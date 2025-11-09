"""Schema type definitions for Open Payments."""
from enum import Enum
from typing import Literal

class ProductFeeResponsibilityType(str, Enum):
    """Who pays the transaction fees."""
    Seller = "seller"
    Buyer = "buyer"

class RenewalType(str, Enum):
    """Renewal frequency types."""
    Daily = "daily"
    Weekly = "weekly"
    Monthly = "monthly"
    Yearly = "yearly"
    OneTime = "onetime"

class ProductType(str, Enum):
    """Product types."""
    OneTime = "onetime"
    Subscription = "subscription"
    Recurring = "recurring"
