"""Hop Sauna

SPDX-FileCopyrightText: Copyright (C) Whythawk and Hop Sauna Authors ask@whythawk.com
SPDX-License-Identifier: AGPL-3.0-or-later

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http:#www.gnu.org/licenses/>.

"""

from typing import Optional, Any
from typing_extensions import Self
from ulid import ULID
from pydantic import (
    ConfigDict,
    Field,
    model_validator,
)
from datetime import datetime

from app.schemas.base_schema import BaseSchema, CountryType
from app.schema_types import ProductFeeResponsibilityType, RenewalType


class OpenOrderBase(BaseSchema):
    # PRODUCT DETAILS
    product_id: Optional[ULID] = Field(None, description="Order is of this Product.")
    price_id: Optional[ULID] = Field(None, description="Order is of this specific Price.")
    country: CountryType = Field(..., description="Buyer country. This must be an ISO country code.")
    # https://openpayments.dev/guides/outgoing-grant-future-payments/#about-the-interval
    renewal: Optional[RenewalType] = Field(
        None,
        description="Order is available as a periodic release, of a particular frequency or condition.",
    )
    renewal_periods: Optional[int] = Field(
        None,
        description="Count of how many times this Order will be automatically renewed when the purchaser buys (i.e. they're committing to this).",
    )
    end: Optional[datetime] = Field(
        None,
        description="Date when this Order will end (i.e. for continuing / repeating deliveries based on this order).",
    )
    completed: bool = Field(False, description="Current completion state for this Order.")
    cancelled: bool = Field(False, description="Current cancellation state for this Order.")
    fees: ProductFeeResponsibilityType = Field(
        default=ProductFeeResponsibilityType.Seller,
        description="Who will pay the transaction fees? Default is the seller.",
    )
    # BUYER DETAILS
    buyer_id: Optional[ULID] = Field(None, description="Order is associated with this Buyer / Wallet.")
    creator_id: Optional[ULID] = Field(
        None, description="Order is associated with this Creator. Only for logged-in, with local account."
    )
    # ORDER WORKFLOW
    incoming_payments: Optional[list[dict[str, Any]]] = Field(
        [], description="Incoming payment resource list of key-value pairs. May be multiple if more than one request."
    )
    incoming_quotes: Optional[list[dict[str, Any]]] = Field(
        [], description="Incoming quote resource list of key-value pairs. May be multiple if more than one request."
    )
    interactive_outgoings: Optional[list[dict[str, Any]]] = Field(
        [],
        description="Interactive outgoing resource list of key-value pairs. May be multiple if more than one request.",
    )
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_conditions(self) -> Self:
        if self.renewal_periods is not None and self.renewal is None:
            raise ValueError("Set `renewal` when setting `renewal_periods`.")
        return self


class OpenOrderCreate(OpenOrderBase):
    pass


class OpenOrderUpdate(OpenOrderBase):
    id: ULID = Field(..., description="Automatically generated unique identity.")
    updated: Optional[datetime] = Field(None, description="Automatically generated date was updated.")


class OpenOrder(OpenOrderUpdate):
    created: datetime = Field(..., description="Automatically generated date was first created.")
    updated: datetime = Field(..., description="Automatically generated date was last updated.")
