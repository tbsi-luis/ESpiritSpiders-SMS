@echo off
REM Test Script for Comprehensive Document Output API
REM This script tests both JSON and document endpoints

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║          AI ANALYZER - COMPREHENSIVE DOCUMENT TEST SCRIPT             ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

set API_URL=http://localhost:8000/api/ai/preconstruction
set INPUT_FILE=sample_project_request.json
set JSON_OUTPUT=response_json.json
set DOCUMENT_OUTPUT=response_document.txt

echo 📁 Input File: %INPUT_FILE%
echo 📊 API URL: %API_URL%
echo.

REM Check if input file exists
if not exist %INPUT_FILE% (
    echo ❌ ERROR: %INPUT_FILE% not found!
    echo.
    exit /b 1
)

echo ✅ Input file found
echo.

REM TEST 1: JSON Endpoint
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║ TEST 1: JSON Response Endpoint                                        ║
echo ║ GET: %API_URL%/analyze                                              ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔄 Sending request...
echo.

curl -X POST "%API_URL%/analyze" ^
  -H "Content-Type: application/json" ^
  -d @%INPUT_FILE% ^
  -o %JSON_OUTPUT% ^
  -w "HTTP Status: %%{http_code}\n"

echo.
if exist %JSON_OUTPUT% (
    echo ✅ Response saved to: %JSON_OUTPUT%
    echo 📊 File size: 
    for %%A in (%JSON_OUTPUT%) do (
        echo     %%~zA bytes
    )
) else (
    echo ❌ Failed to get JSON response
)
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM TEST 2: Document Endpoint (with project name)
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║ TEST 2: Comprehensive Document Endpoint                              ║
echo ║ GET: %API_URL%/analyze/document?project_name=BGC Tower              ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔄 Sending request...
echo.

curl -X POST "%API_URL%/analyze/document?project_name=BGC%%20Commercial%%20Tower" ^
  -H "Content-Type: application/json" ^
  -d @%INPUT_FILE% ^
  -o %DOCUMENT_OUTPUT% ^
  -w "HTTP Status: %%{http_code}\n"

echo.
if exist %DOCUMENT_OUTPUT% (
    echo ✅ Document saved to: %DOCUMENT_OUTPUT%
    echo 📋 File size:
    for %%A in (%DOCUMENT_OUTPUT%) do (
        echo     %%~zA bytes
    )
    echo.
    echo 📄 Document Preview (first 50 lines):
    echo ───────────────────────────────────────────────────────────────────────
    setlocal enabledelayedexpansion
    set line_count=0
    for /f "tokens=*" %%L in (%DOCUMENT_OUTPUT%) do (
        set /a line_count+=1
        if !line_count! leq 50 (
            echo %%L
        )
    )
    echo ───────────────────────────────────────────────────────────────────────
) else (
    echo ❌ Failed to get document response
)
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM TEST 3: Document Endpoint (without workers)
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║ TEST 3: Document Without Worker Recommendations                      ║
echo ║ GET: %API_URL%/analyze/document?include_workers=false               ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔄 Sending request...
echo.

curl -X POST "%API_URL%/analyze/document?include_workers=false" ^
  -H "Content-Type: application/json" ^
  -d @%INPUT_FILE% ^
  -o response_no_workers.txt ^
  -w "HTTP Status: %%{http_code}\n"

echo.
if exist response_no_workers.txt (
    echo ✅ Document saved to: response_no_workers.txt
    for %%A in (response_no_workers.txt) do (
        echo 📋 File size: %%~zA bytes
    )
) else (
    echo ❌ Failed to get document response
)
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM TEST 4: Health Check
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║ TEST 4: API Health Check                                             ║
echo ║ GET: %API_URL%/health                                               ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo 🔄 Checking API health...
echo.

curl -X GET "%API_URL%/health" ^
  -H "Content-Type: application/json" ^
  -w "\nHTTP Status: %%{http_code}\n"

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                        TEST SUMMARY                                   ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo ✅ Tests completed!
echo.
echo Output Files Generated:
if exist %JSON_OUTPUT% (
    echo   ✅ %JSON_OUTPUT% (JSON response)
)
if exist %DOCUMENT_OUTPUT% (
    echo   ✅ %DOCUMENT_OUTPUT% (Comprehensive document)
)
if exist response_no_workers.txt (
    echo   ✅ response_no_workers.txt (Document without workers)
)
echo.
echo 📚 Next Steps:
echo   1. Review %JSON_OUTPUT% for JSON structure
echo   2. Review %DOCUMENT_OUTPUT% for formatted report
echo   3. Compare response_no_workers.txt with full document
echo   4. Check API_USAGE_QUICK_START.py for integration examples
echo.
echo ═══════════════════════════════════════════════════════════════════════════
