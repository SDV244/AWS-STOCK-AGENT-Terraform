import httpx
from jose import jwk, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    from app.config import settings
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        keys   = await _get_cognito_public_keys(settings)

        public_key = None
        for key in keys:
            if key["kid"] == header["kid"]:
                public_key = jwk.construct(key)
                break

        if not public_key:
            raise HTTPException(status_code=401, detail="Public key not found")

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def _get_cognito_public_keys(settings) -> list:
    url = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()["keys"]


def verify_token_sync(token: str) -> dict:
    from app.config import settings   # local import avoids circular dependency

    url = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    resp = httpx.get(url)
    keys = resp.json()["keys"]

    header     = jwt.get_unverified_header(token)
    public_key = None
    for key in keys:
        if key["kid"] == header["kid"]:
            public_key = jwk.construct(key)
            break

    if not public_key:
        raise ValueError("Public key not found")

    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=settings.cognito_client_id,
    )
    return payload