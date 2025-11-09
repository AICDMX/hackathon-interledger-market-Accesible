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

from typing import Optional
from typing_extensions import Self
from ulid import ULID
from pydantic import (
    ConfigDict,
    Field,
    model_validator,
)
from datetime import datetime

from app.schemas.base_schema import BaseSchema, CountryType, CurrencyType
from app.schema_types import ProductFeeResponsibilityType, ProductType


class OpenReceiptBase(BaseSchema):
    # PRODUCT DETAILS
    product_id: Optional[ULID] = Field(None, description="Receipt is of this Product.")
    price_id: Optional[ULID] = Field(None, description="Receipt is of this specific Price.")
    type: ProductType = Field(
        default=ProductType.OneTime, description="Defined Product types, default is 'OneTime' for one-time payment."
    )
    country: CountryType = Field(..., description="Buyer country. This must be an ISO country code.")
    end: Optional[datetime] = Field(
        None,
        description="Date when this Receipt will end (i.e. for continuing / repeating deliveries based on this order).",
    )
    fees: ProductFeeResponsibilityType = Field(
        default=ProductFeeResponsibilityType.Seller,
        description="Who will pay the transaction fees? Default is the seller.",
    )
    # BUYER DETAILS
    buyer_id: Optional[ULID] = Field(None, description="Receipt is associated with this Buyer / Wallet.")
    creator_id: Optional[ULID] = Field(
        None, description="Receipt is associated with this Creator. Only for logged-in, with local account."
    )
    # ORDER WORKFLOW
    order_id: Optional[ULID] = Field(None, description="Receipt is of this Order.")
    amount: str = Field(..., description="Price is an unsigned 64-bit integer amount, represented as a string.")
    assetCode: CurrencyType = Field(..., description="This must be an ISO4217 currency code.")
    assetScale: int = Field(
        ..., description="Number of decimal places defining the scale of the smallest divisible currency unit."
    )
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_conditions(self) -> Self:
        if self.renewal_periods is not None and self.renewal is None:
            raise ValueError("Set `renewal` when setting `renewal_periods`.")
        return self


class OpenReceiptCreate(OpenReceiptBase):
    pass


class OpenReceiptUpdate(OpenReceiptBase):
    id: ULID = Field(..., description="Automatically generated unique identity.")
    updated: Optional[datetime] = Field(None, description="Automatically generated date was updated.")


class OpenReceipt(OpenReceiptUpdate):
    created: datetime = Field(..., description="Automatically generated date was first created.")
    updated: datetime = Field(..., description="Automatically generated date was last updated.")
