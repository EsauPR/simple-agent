import logging
from fastapi import APIRouter, HTTPException
from src.schemas.auth import LoginRequest, LoginResponse
from src.services.auth_service import auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Exchange client credentials for access token"""
    try:
        token_response = await auth_service.get_token(
            request.client_id, request.client_secret
        )

        return LoginResponse(
            access_token=token_response["access_token"],
            token_type=token_response.get("token_type", "Bearer"),
            expires_in=token_response.get("expires_in", 3600),
        )
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=401, detail=f"Authentication failed: {str(e)}"
        )
