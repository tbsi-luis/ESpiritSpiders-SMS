# Testing the Comprehensive Document Output API

## Quick Start

### Prerequisites
1. **FastAPI Server Running**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Sample Data Available**
   - `sample_project_request.json` - Complete test project data

### Test Files Provided

#### 1. **sample_project_request.json**
Complete sample request with:
- Detailed project description (BGC Commercial Tower)
- Full BOQ with materials and quantities
- Architectural plans summary
- Complete project schedule
- 8 sample workers with varied trades and experience

#### 2. **test_endpoints.ps1** (PowerShell)
Interactive PowerShell script with:
- Color-coded output
- 4 test scenarios
- Live preview of document output
- File size reporting
- Status indicators

**Usage:**
```powershell
cd C:\Users\bandivas_l\Desktop\ESpritSpiders\api
.\test_endpoints.ps1
```

#### 3. **test_endpoints.bat** (Batch)
Windows batch script with:
- Simple text output
- 4 test scenarios
- File generation
- Summary report

**Usage:**
```batch
cd C:\Users\bandivas_l\Desktop\ESpritSpiders\api
test_endpoints.bat
```

---

## Testing Scenarios

### Scenario 1: JSON Response Endpoint
**Endpoint:** `POST /api/ai/preconstruction/analyze`

**What it tests:**
- Original JSON endpoint functionality
- Request validation
- Analysis processing
- Response structure

**Expected Output:**
- `response_json.json` - Complete JSON response

**What you'll see:**
```json
{
  "input_evaluation": {...},
  "project_summary": {...},
  "work_packages": [...],
  "manpower_curve": [...],
  "labor_cost_estimate": {...},
  "skill_gap_analysis": {...},
  "risk_analysis": {...},
  ...
}
```

---

### Scenario 2: Comprehensive Document Endpoint
**Endpoint:** `POST /api/ai/preconstruction/analyze/document?project_name=BGC%20Commercial%20Tower`

**What it tests:**
- New document endpoint
- Project name parameter
- Document generation
- Formatting and sections

**Expected Output:**
- `response_document.txt` - Professionally formatted 2,000-4,000 line document

**What you'll see:**
```
====================================================================================================
                            ESPIRIT SPIDERS CONSTRUCTION
                PRE-CONSTRUCTION PHASE MANPOWER ANALYSIS REPORT
====================================================================================================

PROJECT: BGC Commercial Tower
REPORT GENERATED: November 24, 2025 at 14:30:45

[11 major sections with formatted data...]
```

---

### Scenario 3: Document Without Workers
**Endpoint:** `POST /api/ai/preconstruction/analyze/document?include_workers=false`

**What it tests:**
- Document generation without worker section
- Optional parameter handling
- Adaptive section rendering

**Expected Output:**
- `response_no_workers.txt` - Document without worker recommendations

**What you'll see:**
- Same as Scenario 2 but missing the "WORKER DEPLOYMENT RECOMMENDATIONS" section

---

### Scenario 4: API Health Check
**Endpoint:** `GET /api/ai/preconstruction/health`

**What it tests:**
- API availability
- Service status
- Model identification

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "AI Adaptive Project Analyzer",
  "model": "gpt-4",
  "timestamp": "2025-11-24T14:30:45.123456"
}
```

---

## Manual Testing with cURL

### Test 1: JSON Endpoint
```bash
curl -X POST "http://localhost:8000/api/ai/preconstruction/analyze" \
  -H "Content-Type: application/json" \
  -d @sample_project_request.json > response_json.json
```

### Test 2: Document with Project Name
```bash
curl -X POST "http://localhost:8000/api/ai/preconstruction/analyze/document?project_name=BGC%20Tower" \
  -H "Content-Type: application/json" \
  -d @sample_project_request.json > response_document.txt
```

### Test 3: Document Without Workers
```bash
curl -X POST "http://localhost:8000/api/ai/preconstruction/analyze/document?include_workers=false" \
  -H "Content-Type: application/json" \
  -d @sample_project_request.json > response_no_workers.txt
```

### Test 4: Health Check
```bash
curl -X GET "http://localhost:8000/api/ai/preconstruction/health"
```

---

## Manual Testing with Python

### Test All Scenarios
```python
import requests
import json

API_URL = "http://localhost:8000/api/ai/preconstruction"

# Load sample data
with open('sample_project_request.json', 'r') as f:
    project_data = json.load(f)

# Test 1: JSON endpoint
print("Testing JSON endpoint...")
response = requests.post(f"{API_URL}/analyze", json=project_data)
with open('response_json.json', 'w') as f:
    json.dump(response.json(), f, indent=2)
print(f"✅ Status: {response.status_code}")

# Test 2: Document with project name
print("Testing document endpoint...")
response = requests.post(
    f"{API_URL}/analyze/document?project_name=BGC%20Tower",
    json=project_data
)
with open('response_document.txt', 'w') as f:
    f.write(response.text)
print(f"✅ Status: {response.status_code}")

# Test 3: Document without workers
print("Testing document without workers...")
response = requests.post(
    f"{API_URL}/analyze/document?include_workers=false",
    json=project_data
)
with open('response_no_workers.txt', 'w') as f:
    f.write(response.text)
print(f"✅ Status: {response.status_code}")

# Test 4: Health check
print("Testing health check...")
response = requests.get(f"{API_URL}/health")
print(f"✅ Status: {response.status_code}")
print(f"Health: {response.json()}")
```

---

## Manual Testing with JavaScript/Node.js

### Test Document Endpoint
```javascript
const fetch = require('node-fetch');
const fs = require('fs');

const API_URL = 'http://localhost:8000/api/ai/preconstruction';
const projectData = JSON.parse(fs.readFileSync('sample_project_request.json', 'utf8'));

// Test document endpoint
async function testDocumentEndpoint() {
    console.log('Testing document endpoint...');
    
    const response = await fetch(`${API_URL}/analyze/document?project_name=BGC%20Tower`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
    });
    
    const document = await response.text();
    fs.writeFileSync('response_document.txt', document);
    
    console.log(`✅ Status: ${response.status}`);
    console.log(`✅ Document size: ${document.length} bytes`);
    console.log('✅ Document saved to: response_document.txt');
}

testDocumentEndpoint();
```

---

## Understanding the Sample Project Data

### Project Overview
- **Type:** Commercial Office Building
- **Location:** BGC, Makati
- **Duration:** 64 weeks (18 months)
- **Built-up Area:** 25,000 sqm
- **Budget:** ₱2.5 Billion
- **Labor Budget:** ₱450 Million (18%)

### Project Phases
1. **Site Preparation (Weeks 1-2)**
   - Mobilization, clearing, utilities

2. **Foundation (Weeks 3-10)**
   - Piling, excavation, basement

3. **Structural Frame - Lower (Weeks 11-20)**
   - Formwork, rebar, concrete, steel

4. **Structural Frame - Upper (Weeks 21-30)**
   - Levels 4-5, roof construction

5. **MEP Installation (Weeks 31-50)**
   - Electrical, plumbing, HVAC, fire

6. **Interior Finishes (Weeks 51-60)**
   - Drywall, painting, flooring

7. **Final Finishes (Weeks 61-64)**
   - Tile work, fixtures, commissioning

### Available Workers (8 total)
- W001: Juan Dela Cruz - Structural Steel (95% match)
- W002: Maria Santos - Carpentry (85% match)
- W003: Pedro Garcia - Electrical (90% match)
- W004: Ana Reyes - HVAC/Mechanical (88% match)
- W005: Carlos Mendoza - Safety/QC (92% match)
- W006: Rommel Cruz - General Laborers (80% match)
- W007: Ricardo Santos - Concrete (87% match)
- W008: Antonio Villanueva - Masonry/Cladding (82% match)

---

## Expected Results

### Document Generation
✅ Both endpoints should return HTTP 200
✅ Document should contain all 11 sections
✅ File sizes typically 5-15 KB for plain text

### Document Sections
✅ Header with company branding
✅ Executive summary with project details
✅ Work breakdown structure
✅ Weekly manpower breakdown (tabular)
✅ Cost analysis with PHP amounts
✅ Risk assessment with mitigations
✅ Worker recommendations (when included)
✅ Clarification questions
✅ Footer with metadata

### Performance
✅ Response time: < 120 seconds per request
✅ Generation overhead: 50-100ms
✅ No errors or exceptions

---

## Troubleshooting

### API Not Responding
```
Error: Connection refused
Solution: Ensure FastAPI server is running (python -m uvicorn main:app --reload)
```

### Missing sample_project_request.json
```
Error: File not found
Solution: Create the file using the sample data provided
```

### Timeout on Request
```
Error: Request timeout
Solution: Some projects may take longer; increase timeout to 120+ seconds
```

### Invalid JSON Response
```
Error: JSON decode error
Solution: Check that Content-Type header is application/json
```

### Empty Document Output
```
Error: Document is empty
Solution: Check that project_description is not empty in request
```

---

## Verification Checklist

Before deploying to production:

- [ ] FastAPI server starts without errors
- [ ] Health endpoint returns 200 with correct service info
- [ ] JSON endpoint returns structured data
- [ ] Document endpoint returns formatted text
- [ ] Document contains all 11 sections
- [ ] Worker recommendations section appears/disappears based on parameter
- [ ] Project name appears in document header (if provided)
- [ ] PHP currency formatting is correct (₱ with thousands separators)
- [ ] All sections are properly formatted with box borders
- [ ] No syntax errors or exceptions in logs

---

## Performance Testing

### Load Testing
```bash
# Simple load test with 5 concurrent requests
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/ai/preconstruction/analyze/document \
    -H "Content-Type: application/json" \
    -d @sample_project_request.json &
done
wait
```

### Stress Testing
Monitor API performance under load:
- Response times
- Memory usage
- CPU usage
- OpenAI API quota consumption

---

## Integration Testing Checklist

- [ ] JSON endpoint returns valid PreConstructionAnalysisResponse
- [ ] Document endpoint returns plain text
- [ ] Project name parameter works
- [ ] include_workers parameter works
- [ ] Error handling returns proper HTTP codes
- [ ] Validation errors return 400
- [ ] Server errors return 500
- [ ] Service unavailable returns 503

---

## Next Steps After Testing

1. **Review Generated Files**
   - Compare JSON structure with documentation
   - Review document formatting and readability
   - Check worker recommendations accuracy

2. **Integration Development**
   - Use API_USAGE_QUICK_START.py code examples
   - Implement file download in frontend
   - Setup email delivery pipeline
   - Create PDF conversion workflow

3. **Production Deployment**
   - Set environment variables
   - Configure logging
   - Setup monitoring
   - Document API for users

4. **User Training**
   - Share DOCUMENT_OUTPUT_GUIDE.md
   - Demonstrate new endpoint
   - Show example outputs
   - Provide troubleshooting guide

---

## Support & Documentation

- **DOCUMENT_OUTPUT_GUIDE.md** - Complete user guide
- **API_USAGE_QUICK_START.py** - 12 code examples
- **EXAMPLE_COMPREHENSIVE_DOCUMENT.txt** - Sample output
- **README_DOCUMENT_OUTPUT.md** - Feature overview

---

## Questions?

Refer to the comprehensive documentation or check the example outputs included with this implementation.

Happy testing! 🚀
