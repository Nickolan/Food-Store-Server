import logging
import time
from typing import Dict, List

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("app.core.rate_limiter")

AUTH_ENDPOINTS = {
    "/api/v6/auth/token",
    "/api/v6/auth/",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        max_attempts: int = 5,
        window_seconds: int = 900,
    ) -> None:
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method.upper()

        if method == "POST" and path in AUTH_ENDPOINTS:
            ip = self._get_client_ip(request)
            self._clean_expired(ip)

            current_attempts = len(self.attempts.get(ip, []))
            if current_attempts >= self.max_attempts:
                logger.warning("Rate limit alcanzado. ip=%s, intentos=%s, max=%s", ip, current_attempts, self.max_attempts)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            f"Demasiados intentos fallidos. "
                            f"Intentá nuevamente en {self.window_seconds // 60} minutos."
                        )
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )

            response = await call_next(request)

            if response.status_code == 401:
                if ip not in self.attempts:
                    self.attempts[ip] = []
                self.attempts[ip].append(time.time())
                logger.debug("Intento fallido. ip=%s, intentos_actuales=%s", ip, len(self.attempts[ip]))

            elif response.status_code in (200, 201):
                if ip in self.attempts:
                    del self.attempts[ip]
                    logger.debug("Login exitoso — contador reseteado. ip=%s", ip)

            return response

        return await call_next(request)

    def _clean_expired(self, ip: str) -> None:
        """Elimina timestamps fuera de la ventana de tiempo."""
        if ip not in self.attempts:
            return
        cutoff = time.time() - self.window_seconds
        self.attempts[ip] = [t for t in self.attempts[ip] if t > cutoff]
        if not self.attempts[ip]:
            del self.attempts[ip]

    def _get_client_ip(self, request: Request) -> str:
        """Extrae la IP del cliente."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"