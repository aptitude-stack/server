@echo off
setlocal

set "UV_CACHE_DIR=.uv-cache"

uv run alembic upgrade head
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
