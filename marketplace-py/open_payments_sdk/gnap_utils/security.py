"""
Shared class for making secure requests
"""

import hashlib
from logging import Logger
from typing import Sequence
from http_message_signatures import HTTPMessageSigner, algorithms
from http_sf import ser
from httpx import Request
from .hash import HashManager
from .http_signatures import OPKeyResolver, PatchedHTTPSignatureComponentResolver
from .keys import KeyManager


class SecurityBase:
    """
    Base class to provide shared functionality for making authenticated requests
    """

    def __init__(self, keyid: str, private_key: str, logger: Logger):
        self.key_manager = KeyManager()
        self.hash_manager = HashManager()
        self.http_signatures = HTTPMessageSigner(
            signature_algorithm=algorithms.ED25519,
            key_resolver=OPKeyResolver(keyid=keyid, private_key=private_key),
            component_resolver_class=PatchedHTTPSignatureComponentResolver,
        )
        self.keyid = keyid
        self.private_key = private_key
        self.logger = logger

    def get_auth_header(self, access_token: str) -> dict:
        """
        Prepare Authorization GNAP header
        """
        return {"Authorization": f"GNAP {access_token}"}

    def sign_request(self, message: Request, covered_component_ids: Sequence[str]) -> Request:
        """
        Prepare http signature headers
        """
        self.http_signatures.sign(
            message=message, key_id=self.keyid, covered_component_ids=covered_component_ids, label="sig1"
        )
        return message

    def set_content_digest(self, request: Request) -> Request:
        """
        Compute Digest
        """
        # Ensure request.content is bytes (httpx might return memoryview in some cases)
        # Get content and normalize to bytes immediately
        content = request.content
        if isinstance(content, memoryview):
            content = bytes(content)
        elif not isinstance(content, bytes):
            content = bytes(content) if hasattr(content, '__bytes__') else str(content).encode('utf-8')
        
        # Compute digest - ensure result is bytes
        digest_bytes = hashlib.sha512(content).digest()
        # Explicitly convert to bytes to avoid any memoryview issues
        if not isinstance(digest_bytes, bytes):
            if isinstance(digest_bytes, memoryview):
                digest_bytes = bytes(digest_bytes)
            else:
                digest_bytes = bytes(digest_bytes) if hasattr(digest_bytes, '__bytes__') else str(digest_bytes).encode('utf-8')
        
        # Pass bytes directly to ser() - it will handle base64 encoding
        # Double-check we have bytes before passing to ser()
        assert isinstance(digest_bytes, bytes), f"digest_bytes must be bytes, got {type(digest_bytes)}"
        request.headers["Content-Digest"] = ser({"sha-512": digest_bytes})
        
        # If request.content was memoryview, rebuild request with bytes to prevent issues
        # with http_message_signatures library accessing memoryview
        if isinstance(request.content, memoryview):
            content_bytes = bytes(request.content)
            # Rebuild request with bytes content to ensure http_message_signatures gets bytes
            request = Request(
                method=request.method,
                url=request.url,
                headers=dict(request.headers),
                content=content_bytes,
            )
        
        return request
