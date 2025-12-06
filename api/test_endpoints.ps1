# Test Script for Comprehensive Document Output API
# PowerShell version for testing both JSON and document endpoints

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          AI ANALYZER - COMPREHENSIVE DOCUMENT TEST SCRIPT             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:8000/api/ai/preconstruction"
$INPUT_FILE = "sample_project_request.json"
$JSON_OUTPUT = "response_json.json"
$DOCUMENT_OUTPUT = "response_document.txt"
$NO_WORKERS_OUTPUT = "response_no_workers.txt"

Write-Host "📁 Input File: $INPUT_FILE" -ForegroundColor Yellow
Write-Host "📊 API URL: $API_URL" -ForegroundColor Yellow
Write-Host ""

# Check if input file exists
if (-not (Test-Path $INPUT_FILE)) {
    Write-Host "❌ ERROR: $INPUT_FILE not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Input file found" -ForegroundColor Green
Write-Host ""

# TEST 1: JSON Endpoint
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ TEST 1: JSON Response Endpoint                                        ║" -ForegroundColor Cyan
Write-Host "║ POST: $API_URL/analyze                                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Sending request..." -ForegroundColor Yellow

try {
    $json_content = Get-Content $INPUT_FILE -Raw
    $response = Invoke-WebRequest -Uri "$API_URL/analyze" `
        -Method POST `
        -ContentType "application/json" `
        -Body $json_content `
        -OutFile $JSON_OUTPUT `
        -PassThru
    
    Write-Host "✅ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
    
    if (Test-Path $JSON_OUTPUT) {
        $file_size = (Get-Item $JSON_OUTPUT).Length
        Write-Host "✅ Response saved to: $JSON_OUTPUT" -ForegroundColor Green
        Write-Host "📊 File size: $([math]::Round($file_size/1024, 2)) KB" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# TEST 2: Document Endpoint (with project name)
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ TEST 2: Comprehensive Document Endpoint                              ║" -ForegroundColor Cyan
Write-Host "║ POST: $API_URL/analyze/document?project_name=BGC Tower              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Sending request..." -ForegroundColor Yellow

try {
    $json_content = Get-Content $INPUT_FILE -Raw
    $response = Invoke-WebRequest -Uri "$API_URL/analyze/document?project_name=BGC%20Commercial%20Tower" `
        -Method POST `
        -ContentType "application/json" `
        -Body $json_content `
        -OutFile $DOCUMENT_OUTPUT `
        -PassThru
    
    Write-Host "✅ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
    
    if (Test-Path $DOCUMENT_OUTPUT) {
        $file_size = (Get-Item $DOCUMENT_OUTPUT).Length
        Write-Host "✅ Document saved to: $DOCUMENT_OUTPUT" -ForegroundColor Green
        Write-Host "📋 File size: $([math]::Round($file_size/1024, 2)) KB" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "📄 Document Preview (first 40 lines):" -ForegroundColor Yellow
        Write-Host "───────────────────────────────────────────────────────────────────────" -ForegroundColor Gray
        
        $lines = Get-Content $DOCUMENT_OUTPUT | Select-Object -First 40
        foreach ($line in $lines) {
            Write-Host $line
        }
        
        Write-Host "───────────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# TEST 3: Document Endpoint (without workers)
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ TEST 3: Document Without Worker Recommendations                      ║" -ForegroundColor Cyan
Write-Host "║ POST: $API_URL/analyze/document?include_workers=false               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Sending request..." -ForegroundColor Yellow

try {
    $json_content = Get-Content $INPUT_FILE -Raw
    $response = Invoke-WebRequest -Uri "$API_URL/analyze/document?include_workers=false" `
        -Method POST `
        -ContentType "application/json" `
        -Body $json_content `
        -OutFile $NO_WORKERS_OUTPUT `
        -PassThru
    
    Write-Host "✅ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
    
    if (Test-Path $NO_WORKERS_OUTPUT) {
        $file_size = (Get-Item $NO_WORKERS_OUTPUT).Length
        Write-Host "✅ Document saved to: $NO_WORKERS_OUTPUT" -ForegroundColor Green
        Write-Host "📋 File size: $([math]::Round($file_size/1024, 2)) KB" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# TEST 4: Health Check
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ TEST 4: API Health Check                                             ║" -ForegroundColor Cyan
Write-Host "║ GET: $API_URL/health                                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 Checking API health..." -ForegroundColor Yellow

try {
    $health_response = Invoke-WebRequest -Uri "$API_URL/health" `
        -Method GET `
        -ContentType "application/json" `
        -PassThru
    
    Write-Host "✅ HTTP Status: $($health_response.StatusCode)" -ForegroundColor Green
    
    $health_data = $health_response.Content | ConvertFrom-Json
    Write-Host "✅ Status: $($health_data.status)" -ForegroundColor Green
    Write-Host "✅ Service: $($health_data.service)" -ForegroundColor Green
    Write-Host "✅ Model: $($health_data.model)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                        TEST SUMMARY                                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Output Files Generated:" -ForegroundColor Yellow

if (Test-Path $JSON_OUTPUT) {
    $size = [math]::Round((Get-Item $JSON_OUTPUT).Length/1024, 2)
    Write-Host "   ✅ $JSON_OUTPUT ($size KB) - JSON response" -ForegroundColor Green
}

if (Test-Path $DOCUMENT_OUTPUT) {
    $size = [math]::Round((Get-Item $DOCUMENT_OUTPUT).Length/1024, 2)
    Write-Host "   ✅ $DOCUMENT_OUTPUT ($size KB) - Comprehensive document" -ForegroundColor Green
}

if (Test-Path $NO_WORKERS_OUTPUT) {
    $size = [math]::Round((Get-Item $NO_WORKERS_OUTPUT).Length/1024, 2)
    Write-Host "   ✅ $NO_WORKERS_OUTPUT ($size KB) - Document without workers" -ForegroundColor Green
}

Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Review $JSON_OUTPUT for JSON structure" -ForegroundColor Cyan
Write-Host "   2. Review $DOCUMENT_OUTPUT for formatted report" -ForegroundColor Cyan
Write-Host "   3. Compare $NO_WORKERS_OUTPUT with full document" -ForegroundColor Cyan
Write-Host "   4. Check API_USAGE_QUICK_START.py for integration examples" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Testing complete! Check the generated files for results." -ForegroundColor Green
Write-Host ""
