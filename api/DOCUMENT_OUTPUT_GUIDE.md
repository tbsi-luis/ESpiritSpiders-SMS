# Comprehensive Document Output Guide

## Overview

The AI Adaptive Project Analyzer now generates **professional-grade comprehensive documents** instead of just JSON responses. The system automatically formats all analysis data into a well-organized, easy-to-read project report.

---

## Two Output Modes

### 1. **JSON Response** (Original)
**Endpoint:** `POST /api/ai/preconstruction/analyze`

Returns structured JSON data for programmatic use:
```json
{
  "input_evaluation": {...},
  "project_summary": {...},
  "work_packages": [...],
  "manpower_curve": [...],
  "labor_cost_estimate": {...},
  "skill_gap_analysis": {...},
  "risk_analysis": {...},
  "clarification_questions": [...],
  "confidence_score": 0.85,
  "worker_recommendations": [...],
  "generated_at": "2025-11-24T14:30:00",
  "analysis_metadata": {}
}
```

**Use Case:** Integration with other systems, automated processing, data extraction

---

### 2. **Comprehensive Document** (New)
**Endpoint:** `POST /api/ai/preconstruction/analyze/document`

Returns a professionally formatted text document with all analysis sections.

**Query Parameters:**
- `project_name` (optional): Project name for document header
- `include_workers` (optional, default: true): Include worker recommendations section

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/ai/preconstruction/analyze/document?project_name=BGC%20Commercial%20Tower&include_workers=true" \
  -H "Content-Type: application/json" \
  -d '{
    "project_description": "5-storey commercial office building in BGC, Makati...",
    "boq_text": "..."
  }'
```

---

## Document Structure

The comprehensive document includes 11 major sections:

### 1. **Header Section**
- Company branding (ESpirit Spiders Construction)
- Document title
- Project name (if provided)
- Report generation timestamp
- Document version

### 2. **Executive Summary**
- **Project Type**: Classification (Residential, Commercial, Infrastructure)
- **Location**: Geographic location
- **Duration**: Estimated weeks
- **Confidence Level**: Analysis confidence percentage
- **Scope Interpretation**: Summary of project understanding

### 3. **Project Overview**
- Key assumptions used in analysis
- Methodology notes
- Analysis parameters

### 4. **Input Documents Assessment**
- Availability status of:
  - Bill of Quantities (BOQ)
  - Project Plans
  - Schedule/Timeline
- List of missing documents
- Impact on analysis

### 5. **Work Breakdown Structure (WBS)**
Detailed breakdown organized by work package:
```
WP-1: Foundation Work
  Phase:       Site Preparation & Excavation
  Duration:    Weeks 1 - 8 (8 weeks)
  Trades Required (5):
    • Excavation Operators (8 workers) [Weeks 1-8]
    • Carpenters (4 workers) [Weeks 3-8]
    • General Laborers (12 workers) [Weeks 1-8]
    • Safety Officers (2 workers) [Weeks 1-8]
    • Surveyors (1 worker) [Weeks 1-4]
```

### 6. **Manpower Planning & Workforce Curve**
- **Peak Headcount**: Maximum simultaneous workers
- **Minimum Headcount**: Lowest workforce level
- **Average Headcount**: Mean workforce requirement
- **Detailed Weekly Breakdown**: Trade-by-trade weekly allocation

Weekly breakdown example:
```
  Week:           1      2      3      4      5      6      7      8
  ──────────────────────────────────────────────────────────────────
  Excavation      8      8      8      8      6      4      2      0
  Carpenters      0      0      4      6      8      8      6      4
  General Lab    12     12     12     12     12     12     10      8
  TOTAL          20     20     24     26     26     24     18     12
```

### 7. **Labor Cost Estimation & Analysis**
- **Total Labor Cost**: Complete PHP cost estimate
- **Uncertainty Range**: ±% range with bounds
- **Cost Notes**: Assumptions and factors affecting cost
- Regional adjustments (Metro Manila +15%, Provincial -15%)
- Annual escalation rates

Example:
```
ESTIMATED TOTAL LABOR COST:  ₱450,750,000.00
Uncertainty Range:           ±12.5%
  Lower Bound:               ₱394,406,250.00
  Upper Bound:               ₱507,093,750.00
```

### 8. **Skill Gap Analysis**
- **Missing Trade Skills**: Trades not available in current workforce
- **Trades with Shortages**: Trades with insufficient headcount
- **Recommended Hiring Actions**: Specific recruitment recommendations

Example:
```
MISSING TRADE SKILLS:
  ✗ Structural Steel Welding
  ✗ Advanced HVAC Installation

TRADES WITH SHORTAGES:
  ⚠ Carpenters (need 12 additional)
  ⚠ Electrical Specialists (need 5 additional)

RECOMMENDED HIRING ACTIONS:
  1. Immediately recruit 12 carpenters with 2+ years experience
  2. Source 5 electrical specialists certified by MERALCO
  3. Training program for general laborers in material handling
```

### 9. **Risk Assessment & Mitigation**
- **Overall Risk Severity**: CRITICAL, HIGH, MEDIUM, or LOW
- **Identified Risks**: Specific project risks
- **Recommended Mitigations**: Risk response strategies

Example:
```
Overall Risk Severity:  MEDIUM

IDENTIFIED RISKS:
  1. Labor supply shortage in target trades
  2. Seasonal demand peaks affecting availability
  3. Weather impacts on outdoor activities
  4. Equipment utilization conflicts

RECOMMENDED MITIGATIONS:
  1. Establish partnerships with training centers 6 months prior
  2. Implement flexible scheduling and shift rotation
  3. Develop contingency plans for weather delays
  4. Reserve backup equipment with rental partners
```

### 10. **Worker Deployment Recommendations** (Optional)
Workers organized by match quality:

```
★★★ HIGHLY RECOMMENDED (Score ≥ 0.80)
  Juan Dela Cruz (ID: W001)
    Match Score:       95.0%
    Assigned Trades:   Structural Steel, General Labor
    Available Weeks:   1-64
    Recommendation:    Highly recommended. Deploy for: Structural Steel, General Labor

★★ RECOMMENDED (Score 0.60-0.79)
  Maria Santos (ID: W002)
    Match Score:       72.5%
    Assigned Trades:   Carpentry
    Available Weeks:   8-48
    Recommendation:    Recommended with supervision. Can work on: Carpentry
```

### 11. **Clarification Questions for Client**
Questions to improve analysis accuracy:
```
The following information would improve analysis accuracy:

  1. What is the exact site area and accessibility?
  2. Are there any specialized equipment requirements?
  3. Will subcontractors handle specific trades?
  4. What is the preferred shift schedule (8-hour, 10-hour, etc.)?
  5. Are there any union requirements or labor agreements?
```

### 12. **Document Metadata & Footer**
- Generation timestamp
- Confidence score
- System identification
- Legal disclaimer about AI-generated content
- Company footer

---

## Document Features

### Professional Formatting
✓ Box-drawn section headers with `┌─┐` characters
✓ Clear visual hierarchy with spacing
✓ Aligned tabular data
✓ Consistent indentation and structure
✓ 100-character width for readability

### Data Presentation
✓ Currency formatting: PHP amounts with thousands separators
✓ Percentages: Formatted to 1-2 decimal places
✓ Date/time: Full timestamp with timezone
✓ Numbers: Right-aligned for easy scanning
✓ Lists: Clear bullet points and numbering

### Sections are Adaptive
- Sections only appear if data is available
- Worker recommendations only show if workers were provided
- Clarification questions only show if needed
- Risk sections show appropriate severity levels

---

## API Usage Examples

### Example 1: Full Document with Workers

**Request:**
```bash
POST /api/ai/preconstruction/analyze/document?project_name=BGC%20Tower
Content-Type: application/json

{
  "project_description": "5-storey commercial office building in BGC, Makati with 25,000 sqm built-up area",
  "boq_text": "Concrete: 8,500 cubic meters...",
  "plans_text": "Typical floor area 5,000 sqm...",
  "schedule_text": "Foundation: 8 weeks, Superstructure: 20 weeks...",
  "available_workers": [
    {
      "worker_id": "W001",
      "name": "Juan Dela Cruz",
      "trades": ["Structural Steel", "General Laborers"],
      "certifications": ["MERALCO_Accredited", "DOLE_Basic_Training"],
      "reliability_score": 0.95,
      "hourly_rate": 150,
      "availability_start_week": 1,
      "availability_end_week": 64
    }
  ]
}
```

**Response:** (Plain text document)
```
====================================================================================================
                            ESPIRIT SPIDERS CONSTRUCTION
                PRE-CONSTRUCTION PHASE MANPOWER ANALYSIS REPORT
====================================================================================================

PROJECT: BGC Tower
REPORT GENERATED: November 24, 2025 at 14:30:45
DOCUMENT VERSION: 1.0

┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ EXECUTIVE SUMMARY                                                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
...
```

### Example 2: Document Without Worker Recommendations

**Request:**
```bash
POST /api/ai/preconstruction/analyze/document?project_name=Residential%20Complex&include_workers=false
```

Only generates the first 9 sections, excluding the worker recommendations section.

### Example 3: Summary Document Only

**Request:**
```bash
POST /api/ai/preconstruction/analyze/document
```

Without project name, uses generic header. Document is generated but less personalized.

---

## Integration Options

### 1. **Direct File Download**
Frontend can save response as `.txt` file:
```javascript
fetch('/api/ai/preconstruction/analyze/document?project_name=MyProject', {
  method: 'POST',
  body: JSON.stringify(projectData)
})
.then(r => r.text())
.then(text => {
  const element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', 'project_analysis.txt');
  element.click();
});
```

### 2. **Email Delivery**
Send document in email body:
```python
response = requests.post('http://localhost:8000/api/ai/preconstruction/analyze/document', json=data)
email_body = response.text
send_email(to, subject, email_body)
```

### 3. **Print to PDF**
Convert text document to PDF:
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

response = requests.post('.../analyze/document', json=data)
pdf = canvas.Canvas('analysis.pdf', pagesize=letter)
pdf.drawString(50, 800, response.text)
pdf.save()
```

### 4. **Web Display**
Show in browser with `<pre>` tag:
```html
<pre id="analysis-output"></pre>

<script>
fetch('/api/ai/preconstruction/analyze/document', {method: 'POST', body: ...})
  .then(r => r.text())
  .then(text => document.getElementById('analysis-output').textContent = text);
</script>
```

---

## Performance Considerations

- **Response Time**: Minimal overhead (~50-100ms) for document generation on top of analysis time
- **Document Size**: Typical 2,000-4,000 lines (5-10 KB per document)
- **Memory Usage**: All document generation is streaming-compatible
- **Suitable for**: Email, storage, API responses, web display

---

## Customization Options

To customize document output, modify `DocumentGenerator` in `services/document_generator.py`:

- **Change company name**: Modify `self.company_header`
- **Adjust formatting**: Modify section methods (e.g., `_generate_header`)
- **Add sections**: Add new methods and call from `generate_comprehensive_report`
- **Change styling**: Adjust box-drawing characters and spacing
- **Localize content**: Replace English labels with local language

---

## Error Handling

Both endpoints return the same error responses:
- **400**: Invalid request or missing required fields
- **500**: Analysis processing error
- **503**: OpenAI API unavailable

Error messages are included in the HTTP response body.

---

## Conclusion

The comprehensive document output provides a professional, complete analysis report suitable for:
✓ Client presentations
✓ Project archives
✓ Email distribution
✓ Contract attachments
✓ Compliance documentation
✓ Team briefings

All analysis data is preserved and presented in an easily readable format.
