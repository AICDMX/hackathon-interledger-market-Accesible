"""Base schema definitions for Open Payments schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Literal

# Base schema class
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)

# Type aliases for ISO codes
CurrencyType = Literal[
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD",
    "MXN", "SGD", "HKD", "NOK", "TRY", "RUB", "INR", "BRL", "ZAR", "DKK",
    "PLN", "TWD", "THB", "MYR", "PHP", "CZK", "HUF", "ILS", "CLP", "PKR",
    "AED", "COP", "SAR", "IDR", "KRW", "EGP", "IQD", "VND", "NGN", "ARS",
    "BHD", "OMR", "QAR", "KWD", "JOD", "LBP", "BND", "XOF", "XAF", "XPF"
] | str  # Allow any string for flexibility

CountryType = Literal[
    "US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "NL", "BE", "CH", "AT",
    "SE", "NO", "DK", "FI", "PL", "CZ", "IE", "PT", "GR", "LU", "IS", "MT",
    "CY", "EE", "LV", "LT", "SK", "SI", "HU", "RO", "BG", "HR", "ME", "RS",
    "MK", "AL", "BA", "XK", "MD", "UA", "BY", "RU", "TR", "IL", "AE", "SA",
    "KW", "QA", "BH", "OM", "JO", "LB", "IQ", "IR", "EG", "LY", "TN", "DZ",
    "MA", "SD", "ET", "KE", "TZ", "UG", "RW", "GH", "NG", "ZA", "ZW", "BW",
    "NA", "MZ", "MG", "MU", "SC", "KM", "DJ", "ER", "SO", "SS", "CF", "TD",
    "CM", "GQ", "GA", "CG", "CD", "AO", "ZM", "MW", "LS", "SZ", "BJ", "BF",
    "ML", "NE", "SN", "GM", "GN", "GW", "SL", "LR", "CI", "TG", "BJ", "NG",
    "JP", "CN", "KR", "TW", "HK", "SG", "MY", "TH", "VN", "PH", "ID", "BN",
    "MM", "KH", "LA", "MN", "KP", "IN", "PK", "BD", "LK", "MV", "NP", "BT",
    "AF", "KZ", "UZ", "TM", "TJ", "KG", "GE", "AM", "AZ", "IR", "IQ", "SY",
    "JO", "LB", "IL", "PS", "YE", "OM", "AE", "QA", "BH", "KW", "SA", "IQ",
    "MX", "GT", "BZ", "SV", "HN", "NI", "CR", "PA", "CU", "JM", "HT", "DO",
    "PR", "TT", "BB", "GD", "VC", "LC", "DM", "AG", "KN", "BS", "TC", "KY",
    "BR", "AR", "CL", "PE", "CO", "VE", "EC", "BO", "PY", "UY", "GY", "SR",
    "GF", "FK", "NZ", "FJ", "PG", "SB", "VU", "NC", "PF", "WS", "TO", "TV",
    "KI", "NR", "PW", "FM", "MH", "AS", "GU", "MP", "VI", "PR", "DO", "HT",
    "JM", "CU", "BS", "TC", "KY", "VG", "AI", "MS", "GP", "MQ", "BL", "MF",
    "PM", "GL", "SJ", "FO", "AX", "GG", "JE", "IM", "GI", "AD", "MC", "SM",
    "VA", "LI", "MT", "CY"
] | str  # Allow any string for flexibility
