from fastapi import FastAPI
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routes import auth, users, offers , applications

app = FastAPI(
    title="StageFlow API",
    description="API de gestion sécurisée de stages data ",
    version="1.0.0",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offers.router)
app.include_router(applications.router)

@app.get("/health", tags=["Health"])
def read_health():
    return {"status": "healthy"}