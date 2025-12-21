import logging
import httpx
from typing import Optional, Dict, Any
from jose import jwt
from jose.constants import ALGORITHMS
from src.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling Cognito authentication and token validation"""

    def __init__(self):
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_url: Optional[str] = None

    def get_jwks_url(self) -> str:
        """Get JWKS URL from Cognito configuration"""
        if self._jwks_url:
            return self._jwks_url

        if not settings.COGNITO_USER_POOL_ID or not settings.COGNITO_REGION:
            raise ValueError(
                "COGNITO_USER_POOL_ID and COGNITO_REGION must be set to construct JWKS URL"
            )

        self._jwks_url = (
            f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
            f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )

        return self._jwks_url

    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Cognito"""
        if self._jwks_cache:
            return self._jwks_cache

        jwks_url = self.get_jwks_url()
        logger.debug(f"Fetching JWKS from {jwks_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks_cache = response.json()
            return self._jwks_cache

    async def get_token(
        self, client_id: str, client_secret: str, scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange client credentials for access token"""
        token_endpoint = settings.COGNITO_TOKEN_ENDPOINT
        scope = scope or settings.COGNITO_SCOPE

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        }

        logger.debug(f"Requesting token from {token_endpoint}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token against Cognito JWKS"""
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise ValueError("Token missing 'kid' in header")

            # Get JWKS
            jwks = await self.get_jwks()

            # Find the key with matching kid
            key = None
            for jwk_key in jwks.get("keys", []):
                if jwk_key.get("kid") == kid:
                    key = jwk_key
                    break

            if not key:
                raise ValueError(f"Key with kid '{kid}' not found in JWKS")

            # Verify and decode token
            # jwt.decode can work with the JWK dict directly for RS256
            payload = jwt.decode(
                token,
                key,  # Pass the JWK dict directly
                algorithms=[ALGORITHMS.RS256],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": False,  # Cognito tokens may not have aud claim
                    "verify_iss": False,  # We'll verify issuer manually if needed
                },
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise ValueError("Token has expired")
        except jwt.JWTError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}", exc_info=True)
            raise ValueError(f"Token validation error: {str(e)}")


auth_service = AuthService()
