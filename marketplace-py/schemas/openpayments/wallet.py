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
from pydantic import ConfigDict, field_validator, model_validator, HttpUrl, Field
from datetime import datetime

from schemas.base_schema import BaseSchema, CurrencyType
from utilities.openpayments import paymentsparser


class OpenWalletBase(BaseSchema):
    created: Optional[datetime] = Field(None, description="Automatically generated date was first created.")
    address: HttpUrl = Field(..., description="OpenWallet address to this specific creator's account.")
    publicName: Optional[str] = Field(None, description="The public name for this wallet.")
    assetCode: CurrencyType = Field(
        ...,
        description="Code that indicates the underlying asset. This must be an ISO4217 currency code.",
    )
    assetScale: int = Field(
        ...,
        description="Number of decimal places defining the scale of the smallest divisible unit for the given asset code.",
    )
    authServer: Optional[HttpUrl] = Field(None, description="Web URL for this wallet's authentication server.")
    resourceServer: Optional[HttpUrl] = Field(None, description="Web URL for this wallet's resource server.")
    keyID: Optional[str] = Field(None, description="keyID for authorizing signed requests.")
    privateKey: Optional[str] = Field(None, description="Publickey for authorizing signed requests.")
    creator_id: Optional[ULID] = Field(None, description="OpenWallet is associated with this Product.")
    model_config = ConfigDict(from_attributes=True)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if v is None:
            raise ValueError("A valid wallet address is required.")
        return paymentsparser.normalise_wallet_address(wallet_address=v)

    @field_validator("privateKey")
    @classmethod
    def validate_privateKey(cls, v: str) -> str:
        if v is not None:
            return paymentsparser.convert_private_key_to_PEM(private_key=v)
        return v

    @model_validator(mode="after")
    def validate_requirements(self) -> Self:
        if self.privateKey is not None and self.keyID is None:
            raise ValueError("Set `keyID` when setting `privateKey`.")
        return self


class OpenWalletCreate(OpenWalletBase):
    pass


class OpenWalletUpdate(OpenWalletBase):
    id: ULID = Field(..., description="Automatically generated unique identity.")
    updated: Optional[datetime] = Field(None, description="Automatically generated date was updated.")


class OpenWallet(OpenWalletUpdate):
    created: datetime = Field(..., description="Automatically generated date was first created.")
    updated: datetime = Field(..., description="Automatically generated date was last updated.")
