: << 'CMDBLOCK'
@echo off
REM Polyglot wrapper: runs .sh/.py scripts cross-platform
REM Usage: run-hook.cmd <script-name> [args...]
REM The script should be in the same directory as this wrapper
REM
REM This file exists ONLY for Windows dispatch (hooks.json references one
REM script name that works on every OS). It does no env normalization,
REM argument rewriting, or anything else beyond picking python vs bash by
REM extension — don't assume it does more when reading hooks.json cold.

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
