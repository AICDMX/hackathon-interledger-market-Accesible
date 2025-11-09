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
from pydantic import BaseModel, Field, field_validator, AnyUrl
from ulid import ULID
from open_payments_sdk.models.wallet import WalletAddress
from open_payments_sdk.models.resource import Amount

from utilities.openpayments import paymentsparser


class PendingIncomingPaymentTransaction(BaseModel):
    """
    References to recover and continuea pending incoming payment.
    """

    id: ULID = Field(..., description="Tracking key needed to recover the transaction.")
    buyer: WalletAddress = Field(
        ...,
        description="Data for the buyer's open payments wallet",
    )
    seller: WalletAddress = Field(
        ...,
        description="Data for the seller's open payments wallet",
    )
    incoming_payment_id: Optional[AnyUrl] = Field(
        None, description="URL reference to incoming payment generated during initial grant to seller."
    )
    incoming_amount: Optional[Amount] = Field(None, description="Amount requested, including currency code.")
    quote_id: Optional[AnyUrl] = Field(
        None, description="URL reference to quote generated during initial grant to buyer."
    )
    quoted_amount: Optional[Amount] = Field(None, description="Amount quoted, including currency code.")
    interactive_redirect: Optional[AnyUrl] = Field(None, description="URL redirect endpoint to send to the buyer.")
    finish_id: Optional[str] = Field(
        None, description="Random string response from interactive endpoint request, `response.interact.finish`."
    )
    continue_id: Optional[str] = Field(
        None,
        description="Random string response from interactive endpoint request, `response.continue.access_token.value`.",
    )
    continue_url: Optional[AnyUrl] = Field(
        None, description="URL to request a new access key to complete the incoming payment, `response.continue.uri`."
    )


class SellerOpenPaymentAccount(BaseModel):
    """
    Convenience schema to normalise submitted seller open payments data.
    """

    walletAddressUrl: str = Field(
        ...,
        description="URL for the open payments wallet",
    )
    privateKey: str = Field(
        ...,
        description="The types of actions the client instance will take at the RS as an array of strings.",
    )
    keyId: str = Field(
        ...,
        description="The types of actions the client instance will take at the RS as an array of strings.",
    )

    @field_validator("walletAddressUrl", mode="before")
    @classmethod
    def evaluate_wallet_address(cls, walletAddressUrl):
        walletAddressUrl = paymentsparser.normalise_wallet_address(wallet_address=walletAddressUrl)
        return walletAddressUrl

    @field_validator("privateKey", mode="before")
    @classmethod
    def evaluate_private_key(cls, privateKey):
        privateKey = paymentsparser.convert_private_key_to_PEM(private_key=privateKey)
        return privateKey
