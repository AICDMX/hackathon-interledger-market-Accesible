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
from ulid import ULID
from pydantic import ConfigDict, Field
from datetime import datetime

from app.schemas.base_schema import BaseSchema, CurrencyType


class OpenRecipientBase(BaseSchema):
    # RECIPIENT DETAILS
    wallet_id: Optional[ULID] = Field(None, description="Recipient fees were paid into this Wallet.")
    creator_id: Optional[ULID] = Field(None, description="Recipient Creator account.")
    # PRODUCT DETAILS
    product_id: Optional[ULID] = Field(None, description="Payment related to this Product.")
    price_id: Optional[ULID] = Field(None, description="Payment related to this Price.")
    receipt_id: Optional[ULID] = Field(None, description="Payment related to this Receipt.")
    # ORDER WORKFLOW
    amount: str = Field(..., description="Price is an unsigned 64-bit integer amount, represented as a string.")
    assetCode: CurrencyType = Field(..., description="This must be an ISO4217 currency code.")
    assetScale: int = Field(
        ..., description="Number of decimal places defining the scale of the smallest divisible currency unit."
    )
    payment_response: Optional[list[dict[str, Any]]] = Field(
        [], description="Incoming payment resource list of key-value pairs. May be multiple if more than one request."
    )
    model_config = ConfigDict(from_attributes=True)


class OpenRecipientCreate(OpenRecipientBase):
    pass


class OpenRecipientUpdate(OpenRecipientBase):
    id: ULID = Field(..., description="Automatically generated unique identity.")
    updated: Optional[datetime] = Field(None, description="Automatically generated date was updated.")


class OpenRecipient(OpenRecipientUpdate):
    created: datetime = Field(..., description="Automatically generated date was first created.")
    updated: datetime = Field(..., description="Automatically generated date was last updated.")
