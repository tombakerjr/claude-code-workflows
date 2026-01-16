: << 'CMDBLOCK'
@echo off
REM Polyglot wrapper: runs .sh/.py scripts cross-platform
REM Usage: run-hook.cmd <script-name> [args...]
REM The script should be in the same directory as this wrapper

REM Check file extension and run appropriately
set "script=%~1"
set "ext=%~x1"
if /I "%ext%"==".py" (
    python "%~dp0%~1"
) else (
    "C:\Program Files\Git\bin\bash.exe" -l "%~dp0%~1"
)
exit /b
CMDBLOCK

# Unix shell runs from here
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift

# Check extension and run appropriately
case "$SCRIPT_NAME" in
    *.py)
        python3 "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
        ;;
    *)
        "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
        ;;
esac
