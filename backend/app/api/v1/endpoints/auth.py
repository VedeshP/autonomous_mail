# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError

from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.auth import GoogleToken, TokenResponse, RefreshTokenRequest
from app.core.gmail_service import get_gmail_auth_url, exchange_code_and_save_tokens
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/google", response_model=TokenResponse)
def google_auth(
    payload: GoogleToken, 
    db: Session = Depends(get_db)
):
    """
    Verifies the Google ID token sent by the frontend, finds or creates the user,
    and returns a pair of Access and Refresh tokens.
    """
    try:
        # 1. Verify the token with Google's servers
        idinfo = id_token.verify_oauth2_token(
            payload.token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )

        # 2. Extract user info from Google's response
        google_sub = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        # 3. Check if user exists in our database
        user = db.query(User).filter(User.google_sub == google_sub).first()

        # 4. If not, create them!
        if not user:
            user = User(
                google_sub=google_sub,
                email=email,
                full_name=name,
                picture_url=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 5. Generate our internal Access & Refresh Tokens using the UUID
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        # 6. Return them to the frontend
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id
        )

    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
        
        
@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    payload: RefreshTokenRequest, 
    db: Session = Depends(get_db)
):
    """Takes a valid refresh token and returns a new access/refresh token pair."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    try:
        # Decode the refresh token
        token_data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Security Check: Ensure this is actually a refresh token
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
            
        user_id_str = token_data.get("sub")
        if not user_id_str:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    # Check if user still exists and is active
    user = db.query(User).filter(User.id == user_id_str).first()
    if not user or not user.is_active:
        raise credentials_exception

    # Issue a fresh pair of tokens
    new_access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user_id=user.id
    )


# Note the added `db: Session = Depends(get_db)` parameter
@router.get("/gmail/authorize")
def authorize_gmail(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    The frontend calls this (with a valid JWT) when the user clicks 'Connect Gmail'.
    """
    auth_url = get_gmail_auth_url(db=db, user_id=current_user.id) # Passed db here
    return {"auth_url": auth_url}


@router.get("/gmail/callback")
def gmail_callback(request: Request, state: str, code: str, db: Session = Depends(get_db)):
    """
    Google redirects the user here after they click "Allow".
    We grab the code, swap it for tokens, and save it to the DB.
    """
    try:
        # 'state' is the user_id we passed in originally
        user_id = state 
        
        # Call our utility function
        exchange_code_and_save_tokens(db=db, code=code, user_id=user_id)
        
        # Redirect the user back to the frontend dashboard
        return RedirectResponse(url="http://localhost:3000?gmail_connected=true")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect Gmail: {str(e)}")
    
    

"""Only for dev usage"""

class DevLoginRequest(BaseModel):
    email: str

@router.post("/dev-login", response_model=TokenResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    """
    DEV ONLY: Instantly issues tokens for a given email if they exist.
    Do NOT deploy this to production!
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id
    )