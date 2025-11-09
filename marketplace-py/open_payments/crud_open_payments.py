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

from ulid import ULID
from pydantic import AnyUrl
from app.open_payments_sdk.http import HttpClient
from app.open_payments_sdk.client.client import OpenPaymentsClient
from app.open_payments_sdk.api.auth import GrantRequest, Grant, InteractRef
from app.open_payments_sdk.models.resource import (
    IncomingPaymentRequest,
    OutgoingPaymentRequest,
    OutgoingPayment,
    Quote,
    QuoteRequest,
)

from app.core.config import settings
from app.utilities.openpayments import paymentsparser
from app.schemas.openpayments.open_payments import SellerOpenPaymentAccount, PendingIncomingPaymentTransaction


class OpenPaymentsProcessor:
    """
    Core functions for processing open payments on behalf of an instance actor merchant account.

    Based on https://openpayments.dev/concepts/op-flow/

    1. Get recipient's wallet address information
    2. Request an Incoming Payment grant
    3. Create an Incoming Payment
    4. Request a Quote grant
    5. Create a Quote
    6. Request an interactive Outgoing Payment grant
    7. Start interaction with the user
    8. Finish interaction with the user
    9. Request a grant continuation
    10. Create an Outgoing Payment

    The key break is the interactive phase. It is necessary to save the buyer-
    """

    def __init__(
        self,
        *,
        seller: SellerOpenPaymentAccount,
        buyer: str,
        http_client: HttpClient = None,
        redirect_uri: str = settings.DEFAULT_REDIRECT_AFTER_AUTH,
    ) -> None:
        if not http_client:
            http_client = HttpClient(http_timeout=10.0)
        self.http_client = http_client
        self.seller = seller
        self.buyer = paymentsparser.normalise_wallet_address(wallet_address=buyer)
        self.client = OpenPaymentsClient(
            keyid=self.seller.keyId,
            private_key=self.seller.privateKey,
            client_wallet_address=self.seller.walletAddressUrl,
            http_client=self.http_client,
        )
        self.seller_wallet = self.client.wallet.get_wallet_address(self.seller.walletAddressUrl)
        self.buyer_wallet = self.client.wallet.get_wallet_address(self.buyer)
        self.pending_payment = PendingIncomingPaymentTransaction(
            **{"id": ULID(), "seller": self.seller_wallet, "buyer": self.buyer_wallet}
        )
        self.redirect_uri = f"{redirect_uri}{self.pending_payment.id}"

    ###################################################################################################
    # 1. GRANT-MAKING GENERAL UTILITY
    ###################################################################################################

    def request_grant(self, *, grant: str, actions: list[str], endpoint: AnyUrl) -> Grant:
        request = GrantRequest(
            **{
                "access_token": {
                    "access": [
                        {
                            "type": grant,
                            "actions": actions,
                        }
                    ]
                },
                "client": str(self.seller_wallet.id),
            }
        )
        return self.client.grants.post_grant_request(grant_request=request, auth_server_endpoint=str(endpoint))

    ###################################################################################################
    # 2. SELLER INCOMING PAYMENT PROCESS
    ###################################################################################################

    def request_incoming_payment(self, *, amount: int | str):
        """TO THE SELLER"""
        if isinstance(amount, int):
            amount = str(amount)
        # Request a grant
        grant = self.request_grant(
            grant="incoming-payment",
            actions=["create", "read", "read-all", "complete", "list"],
            endpoint=self.seller_wallet.authServer,
        )
        grant = grant.model_dump(exclude_unset=True, mode="json")
        access_token = grant.get("access_token", {}).get("value")
        # Request an incoming payment
        payment = IncomingPaymentRequest(
            **dict(
                walletAddress=str(self.seller_wallet.id),
                incomingAmount=dict(
                    value=amount,
                    assetCode=self.seller_wallet.assetCode.root,
                    assetScale=self.seller_wallet.assetScale.root,
                ),
            )
        )
        return self.client.incoming_payments.post_create_payment(
            payment=payment, resource_server_endpoint=str(self.seller_wallet.resourceServer), access_token=access_token
        )

    ###################################################################################################
    # 3. BUYER QUOTE REQUEST PROCESS
    ###################################################################################################

    def request_quote(self, *, incoming_payment_id: str | AnyUrl) -> Quote:
        """TO THE BUYER"""
        # Request a grant
        grant = self.request_grant(
            grant="quote", actions=["create", "read", "read-all"], endpoint=self.buyer_wallet.authServer
        )
        grant = grant.model_dump(exclude_unset=True, mode="json")
        access_token = grant.get("access_token", {}).get("value")
        # Request a quote for the payment
        quote = QuoteRequest(
            **dict(
                walletAddress=str(self.buyer_wallet.id),
                receiver=str(incoming_payment_id),
                method="ilp",
            )
        )
        return self.client.quotes.post_create_quote(
            quote=quote, resource_server_endpoint=str(self.buyer_wallet.resourceServer), access_token=access_token
        )

    ###################################################################################################
    # 4. REQUEST BUYER INTERACTIVE GRANT FOR PURCHASE
    ###################################################################################################

    def get_purchase_endpoint(self, *, amount: int | str) -> str:
        """
        Implements the first half of the purchase process, requesting 'incoming-payment' and 'quote' grants,
        then requesting - and returning - an interactive payment grant for the buyer.
        """
        if isinstance(amount, int):
            amount = str(amount)
        # 1. Request incoming payment grant for the seller
        incoming_payment_response = self.request_incoming_payment(amount=amount)
        self.pending_payment.incoming_payment_id = incoming_payment_response.id
        # 2. Request quote grant for the buyer
        quote_response = self.request_quote(incoming_payment_id=incoming_payment_response.id)
        self.pending_payment.quote_id = quote_response.id
        # 3. Request an interactive payment endpoint for the buyer
        # Request a grant
        grant_request = GrantRequest(
            **dict(
                access_token=dict(
                    access=[
                        dict(
                            identifier=str(self.buyer_wallet.id),
                            type="outgoing-payment",
                            actions=["create", "read", "read-all", "list", "list-all"],
                            limits=dict(
                                debitAmount=dict(
                                    assetCode=quote_response.debitAmount.assetCode.root,
                                    assetScale=quote_response.debitAmount.assetScale.root,
                                    value=quote_response.debitAmount.value,
                                ),
                            ),
                        ),
                    ],
                ),
                client=str(self.seller_wallet.id),
                interact=dict(
                    start=["redirect"],
                    finish=dict(
                        method="redirect",
                        uri=self.redirect_uri,
                        nonce=str(self.pending_payment.id),
                    ),
                ),
            )
        )
        # Request the interactive endpoint
        # TODO: db save of the quote and interactive responses to retrieve later to complete the purchase
        interactive_response = self.client.grants.post_grant_request(
            grant_request=grant_request, auth_server_endpoint=str(self.buyer_wallet.authServer)
        )
        self.pending_payment.interactive_redirect = interactive_response.root.interact.redirect
        self.pending_payment.finish_id = interactive_response.root.interact.finish
        self.pending_payment.continue_id = interactive_response.root.cont.access_token.value
        self.pending_payment.continue_url = interactive_response.root.cont.uri
        return interactive_response.root.interact.redirect

    ###################################################################################################
    # 5. COMPLETE OUTGOING PAYMENT
    ###################################################################################################

    def complete_payment(
        self, interact_ref: str, received_hash: str, pending_payment: PendingIncomingPaymentTransaction
    ) -> OutgoingPayment:
        """
        After purchaser approves interactive payment, webhook will receive confirmation permitting continuation.

        Use `key` to retrieve the original interactive grant request, and `interact_ref` to complete payment.
        """
        # First validate the interactive response hash
        if not paymentsparser.verify_response_hash(
            incoming_payment_id=pending_payment.id,
            finish_id=pending_payment.finish_id,
            interact_ref=interact_ref,
            auth_server_url=str(pending_payment.buyer.authServer),
            received_hash=received_hash,
        ):
            raise ValueError(f"Hash invalid for pending payment `{pending_payment.incoming_payment_id}`")
        # Request a grant continuation
        grant_request = self.client.grants.post_grant_continuation_request(
            interact_ref=InteractRef(**dict(interact_ref=interact_ref)),
            continue_uri=str(pending_payment.continue_url),
            access_token=pending_payment.continue_id,
        )
        access_token = grant_request.access_token.value
        # Create an outgoing payment from the `buyer`
        outgoing_payment_request = OutgoingPaymentRequest(
            **dict(walletAddress=str(pending_payment.buyer.id), quoteId=pending_payment.quote_id, metadata={})
        )
        return self.client.outgoing_payments.post_create_payment(
            payment=outgoing_payment_request,
            resource_server_endpoint=str(pending_payment.buyer.resourceServer),
            access_token=access_token,
        )
