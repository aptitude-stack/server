@echo off
setlocal

set "LOG_LEVEL=DEBUG"
set "UVICORN_RELOAD=false"
set "UV_CACHE_DIR=.uv-cache"

echo Starting FastAPI dev server in debug mode
echo   API:   http://127.0.0.1:8000
echo   Docs:  http://127.0.0.1:8000/docs
echo   Level: DEBUG
echo   Stop:  Ctrl+C
echo.

uv run python -m app.main
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
