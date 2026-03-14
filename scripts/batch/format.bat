@echo off
setlocal

set "UV_CACHE_DIR=.uv-cache"

uv run --extra dev ruff format . %*
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
