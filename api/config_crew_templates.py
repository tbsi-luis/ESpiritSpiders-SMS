"""
Configuration file for Philippine construction trade crew templates and labor rates.
Used by the AI Adaptive Project Analyzer for manpower forecasting.
All rates are in Philippine Peso (PHP) as of November 2024.
"""

# Trade definitions with typical crew compositions and daily rates (in PHP)
# Based on Philippine construction standards and DOLE wage rates
TRADE_DEFINITIONS = {
    "Cabinetry & Carpentry": {
        "daily_rate_php": 1500,
        "typical_crew_size": 3,
        "skills": ["wood_working", "furniture_making", "installation"],
        "certifications": ["PCC_License", "Safety_Certificate"]
    },
    "Concrete/Mason Works": {
        "daily_rate_php": 1200,
        "typical_crew_size": 6,
        "skills": ["concreting", "block_laying", "plastering"],
        "certifications": ["DOLE_Certificate", "Safety_Training"]
    },
    "Electrical Installation": {
        "daily_rate_php": 1800,
        "typical_crew_size": 3,
        "skills": ["wiring", "panel_installation", "diagnostics"],
        "certifications": ["PEC_License", "MERALCO_Accredited"]
    },
    "Plumbing & Waterproofing": {
        "daily_rate_php": 1600,
        "typical_crew_size": 3,
        "skills": ["pipe_installation", "waterproofing", "troubleshooting"],
        "certifications": ["PHREB_Certificate", "Plumbing_License"]
    },
    "Steel Works & Welding": {
        "daily_rate_php": 1700,
        "typical_crew_size": 4,
        "skills": ["welding", "steel_fixing", "rigging"],
        "certifications": ["AWS_Certification", "Welder_License"]
    },
    "Formwork & Carpentry": {
        "daily_rate_php": 1400,
        "typical_crew_size": 5,
        "skills": ["formwork_assembly", "leveling", "temporary_works"],
        "certifications": ["DOLE_Certificate", "Safety_Training"]
    },
    "Painting & Finishing": {
        "daily_rate_php": 1100,
        "typical_crew_size": 4,
        "skills": ["painting", "surface_prep", "coating_application"],
        "certifications": ["Safety_Certificate"]
    },
    "Landscaping & Grounds": {
        "daily_rate_php": 900,
        "typical_crew_size": 5,
        "skills": ["planting", "irrigation", "hardscaping"],
        "certifications": ["Safety_Certificate"]
    },
    "Excavation & Earthworks": {
        "daily_rate_php": 1300,
        "typical_crew_size": 8,
        "skills": ["excavation", "compaction", "site_prep"],
        "certifications": ["Heavy_Equipment_Cert", "Safety_Training"]
    },
    "Rebar & Reinforcement": {
        "daily_rate_php": 1250,
        "typical_crew_size": 5,
        "skills": ["bar_bending", "fixing", "quality_control"],
        "certifications": ["DOLE_Certificate", "Inspection_Qualified"]
    },
    "Tile & Flooring": {
        "daily_rate_php": 1350,
        "typical_crew_size": 3,
        "skills": ["tile_installation", "grouting", "finishing"],
        "certifications": ["PCC_License", "Quality_Cert"]
    },
    "HVAC & Mechanical": {
        "daily_rate_php": 1900,
        "typical_crew_size": 3,
        "skills": ["ductwork", "equipment_installation", "testing"],
        "certifications": ["HVAC_License", "Mechanical_Cert"]
    },
    "General Laborers": {
        "daily_rate_php": 650,
        "typical_crew_size": 12,
        "skills": ["manual_labor", "material_handling", "site_cleaning"],
        "certifications": ["Safety_Certificate", "DOLE_Basic_Training"]
    },
    "Site Management & Coordination": {
        "daily_rate_php": 2200,
        "typical_crew_size": 2,
        "skills": ["project_coordination", "safety_management", "documentation"],
        "certifications": ["PMP", "DOLE_Safety_Officer", "PCC_Supervisor"]
    }
}

# Default work package templates for common Philippine project types
DEFAULT_WORK_PACKAGES = {
    "Residential": [
        {
            "name": "Site Preparation & Excavation",
            "phase": "Preparation",
            "trades": ["Excavation & Earthworks", "General Laborers", "Site Management & Coordination"],
            "typical_duration_weeks": 2,
            "peak_headcount": 15
        },
        {
            "name": "Foundation & Concrete Works",
            "phase": "Foundation",
            "trades": ["Rebar & Reinforcement", "Formwork & Carpentry", "Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 4,
            "peak_headcount": 25
        },
        {
            "name": "Structural Frame & Steel",
            "phase": "Structure",
            "trades": ["Steel Works & Welding", "Rebar & Reinforcement", "Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 5,
            "peak_headcount": 28
        },
        {
            "name": "MEP Systems Installation",
            "phase": "MEP",
            "trades": ["Electrical Installation", "Plumbing & Waterproofing", "HVAC & Mechanical", "General Laborers"],
            "typical_duration_weeks": 4,
            "peak_headcount": 18
        },
        {
            "name": "Interior Finishes & Fit-out",
            "phase": "Finishes",
            "trades": ["Painting & Finishing", "Tile & Flooring", "Cabinetry & Carpentry", "General Laborers"],
            "typical_duration_weeks": 3,
            "peak_headcount": 18
        }
    ],
    "Commercial": [
        {
            "name": "Site Development & Mobilization",
            "phase": "Preparation",
            "trades": ["Excavation & Earthworks", "General Laborers", "Site Management & Coordination"],
            "typical_duration_weeks": 3,
            "peak_headcount": 16
        },
        {
            "name": "Foundation & Piling",
            "phase": "Foundation",
            "trades": ["Excavation & Earthworks", "Rebar & Reinforcement", "Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 5,
            "peak_headcount": 28
        },
        {
            "name": "Structural Superstructure",
            "phase": "Structure",
            "trades": ["Steel Works & Welding", "Formwork & Carpentry", "Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 7,
            "peak_headcount": 35
        },
        {
            "name": "Building Envelope & Facade",
            "phase": "Envelope",
            "trades": ["Concrete/Mason Works", "Painting & Finishing", "General Laborers"],
            "typical_duration_weeks": 5,
            "peak_headcount": 20
        },
        {
            "name": "MEP Installation",
            "phase": "MEP",
            "trades": ["Electrical Installation", "Plumbing & Waterproofing", "HVAC & Mechanical", "General Laborers"],
            "typical_duration_weeks": 6,
            "peak_headcount": 22
        },
        {
            "name": "Interior Finishes & Commissioning",
            "phase": "Finishes",
            "trades": ["Tile & Flooring", "Painting & Finishing", "Cabinetry & Carpentry", "General Laborers"],
            "typical_duration_weeks": 5,
            "peak_headcount": 20
        }
    ],
    "Infrastructure": [
        {
            "name": "Mobilization & Site Survey",
            "phase": "Preparation",
            "trades": ["Excavation & Earthworks", "General Laborers", "Site Management & Coordination"],
            "typical_duration_weeks": 2,
            "peak_headcount": 12
        },
        {
            "name": "Earthwork & Grading",
            "phase": "Earthwork",
            "trades": ["Excavation & Earthworks", "General Laborers"],
            "typical_duration_weeks": 4,
            "peak_headcount": 18
        },
        {
            "name": "Base Course & Subgrade",
            "phase": "Pavement",
            "trades": ["Excavation & Earthworks", "Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 3,
            "peak_headcount": 16
        },
        {
            "name": "Asphalt/Concrete Pavement",
            "phase": "Pavement",
            "trades": ["Concrete/Mason Works", "General Laborers"],
            "typical_duration_weeks": 4,
            "peak_headcount": 18
        },
        {
            "name": "Utilities & Final Works",
            "phase": "Utilities",
            "trades": ["Electrical Installation", "Plumbing & Waterproofing", "Landscaping & Grounds", "General Laborers"],
            "typical_duration_weeks": 3,
            "peak_headcount": 14
        }
    ]
}

# Confidence level mappings based on document availability
CONFIDENCE_MULTIPLIERS = {
    "has_all": 0.95,          # All documents present
    "has_boq_plans": 0.90,    # BOQ and plans
    "has_boq_schedule": 0.85, # BOQ and schedule
    "has_plans_schedule": 0.80, # Plans and schedule
    "has_boq_only": 0.75,     # Only BOQ
    "has_plans_only": 0.70,   # Only plans
    "has_schedule_only": 0.65, # Only schedule
    "has_description_only": 0.50  # Only description
}

# Risk severity levels and recommended mitigation categories
RISK_CATEGORIES = {
    "CRITICAL": {
        "level": "CRITICAL",
        "mitigation_focus": ["Resource Planning", "Backup Crews", "Schedule Buffer"]
    },
    "HIGH": {
        "level": "HIGH",
        "mitigation_focus": ["Resource Allocation", "Training", "Schedule Review"]
    },
    "MEDIUM": {
        "level": "MEDIUM",
        "mitigation_focus": ["Monitoring", "Contingency", "Communication"]
    },
    "LOW": {
        "level": "LOW",
        "mitigation_focus": ["Standard Practice", "Documentation"]
    }
}

# Worker matching criteria weights
WORKER_MATCH_WEIGHTS = {
    "skill_match": 0.40,        # 40% weight on skills match
    "certification_match": 0.25, # 25% weight on certifications
    "reliability": 0.20,        # 20% weight on attendance/reliability
    "project_similarity": 0.15  # 15% weight on similar project experience
}

# Default assumptions when generating inferred manpower (Philippines-specific)
DEFAULT_ASSUMPTIONS = [
    "Assumed 8-hour work day (5 days per week, Monday-Friday)",
    "Standard crew productivity based on Philippine construction benchmarks",
    "No overtime assumed in baseline plan",
    "Single shift operation",
    "DOLE safety regulations and standards applied",
    "Philippines-based labor rates and classifications",
    "Contingency not included in base estimate",
    "Based on Metro Manila/urban rates; may vary by region",
    "National holidays and local holidays factored separately",
    "Compliance with DOLE, PCC, and local government requirements"
]

# Typical cost escalation factors (Philippines)
COST_ESCALATION_FACTORS = {
    "base_year": 2024,
    "annual_escalation_percent": 7.5,  # Higher inflation in Philippines
    "seasonal_adjustment_percent": 2.0,  # Monsoon season impacts
    "region_adjustment_percent": 0.0,  # Can be adjusted per region
    "metro_manila_premium": 1.15,  # 15% premium for Metro Manila
    "provincial_adjustment": 0.85  # 15% discount for provincial areas
}
