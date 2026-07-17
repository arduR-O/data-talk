from fastapi import APIRouter, HTTPException, Header, Depends
from controllers.auth_controller import AuthController
from schemas.authschemas import SignupRequest, LoginRequest, AuthResponse, GoogleLoginRequest

router = APIRouter()
auth_controller = AuthController()

@router.post("/google", response_model=AuthResponse)
async def google_login(payload: GoogleLoginRequest):
    """Google OAuth login and auto-signup endpoint"""
    result = auth_controller.google_login(payload.id_token)
    
    if result['success']:
        return {
            "message": result['message'],
            "data": result['data']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )

@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: SignupRequest):
    """User registration endpoint"""
    result = auth_controller.signup(user_data.dict())
    
    if result['success']:
        return {
            "message": result['message'],
            "data": result['data']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )

@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """User login endpoint"""
    result = auth_controller.login(credentials.dict())
    
    if result['success']:
        return {
            "message": result['message'],
            "data": result['data']
        }
    else:
        raise HTTPException(
            status_code=result['status_code'],
            detail=result['message']
        )

@router.get("/verify")
async def verify_token(authorization: str = Header(...)):
    """Verify JWT token endpoint"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = auth_controller.verify_token(token)
        user = auth_controller.user_model.find_user_by_id(payload['user_id'])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {
            "message": "Token is valid",
            "data": {
                "user_id": str(user['_id']),
                "email": user['email'],
                "firstName": user['firstName'],
                "lastName": user['lastName']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))