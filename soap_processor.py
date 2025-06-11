import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClinicalGuidelines:
    """Clinical practice guidelines and evidence sources"""
    
    GUIDELINE_SOURCES = {
        'cardiovascular': [
            {'org': 'ACC/AHA', 'topic': 'Hypertension', 'year': 2023},
            {'org': 'ACC/AHA', 'topic': 'Chest Pain', 'year': 2022},
            {'org': 'ESC', 'topic': 'Cardiovascular Disease Prevention', 'year': 2023},
            {'org': 'NICE', 'topic': 'Stable Angina', 'year': 2022}
        ],
        'diagnostic': [
            {'org': 'ACP', 'topic': 'Cardiac Screening', 'year': 2023},
            {'org': 'USPSTF', 'topic': 'Cardiovascular Risk Assessment', 'year': 2022}
        ],
        'preventive': [
            {'org': 'USPSTF', 'topic': 'Aspirin Use', 'year': 2022},
            {'org': 'ACC/AHA', 'topic': 'Primary Prevention', 'year': 2023}
        ]
    }
    
    RISK_CALCULATORS = {
        'cardiovascular': [
            'ASCVD Risk Calculator',
            'Framingham Risk Score',
            'SCORE2 Risk Calculator'
        ],
        'diagnostic': [
            'HEART Score',
            'TIMI Risk Score',
            'GRACE Score'
        ]
    }
    
    RED_FLAGS = {
        'chest_pain': [
            'radiation to arm/jaw',
            'associated shortness of breath',
            'diaphoresis',
            'nausea/vomiting',
            'syncope/near-syncope'
        ],
        'hypertension': [
            'severe elevation (>180/120)',
            'headache',
            'visual changes',
            'neurological symptoms',
            'chest pain'
        ]
    }

@dataclass
class VitalSigns:
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    temperature: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None

    @staticmethod
    def parse_bp(bp_str: str) -> tuple:
        """Parse blood pressure string into systolic and diastolic values"""
        match = re.search(r'(\d+)/(\d+)', bp_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def is_hypertensive(self) -> bool:
        """Check if blood pressure indicates hypertension"""
        if self.blood_pressure:
            systolic, diastolic = self.parse_bp(self.blood_pressure)
            if systolic and diastolic:
                return systolic >= 140 or diastolic >= 90
        return False
    
    def get_bp_category(self) -> str:
        """Categorize blood pressure according to ACC/AHA guidelines"""
        if self.blood_pressure:
            systolic, diastolic = self.parse_bp(self.blood_pressure)
            if systolic and diastolic:
                if systolic >= 180 or diastolic >= 120:
                    return "Hypertensive Crisis"
                elif systolic >= 140 or diastolic >= 90:
                    return "Stage 2 Hypertension"
                elif systolic >= 130 or diastolic >= 80:
                    return "Stage 1 Hypertension"
                elif systolic >= 120 and systolic < 130 and diastolic < 80:
                    return "Elevated"
                else:
                    return "Normal"
        return "Unknown"

@dataclass
class SOAPNote:
    patient_name: str
    age: int
    date: datetime
    provider: str
    visit_type: str
    subjective: str
    objective: Dict[str, Any]
    assessment: List[str]
    plan: Dict[str, List[str]]
    vital_signs: VitalSigns

class SOAPProcessor:
    def __init__(self):
        self.common_symptoms = {
            'chest pain': {
                'diagnoses': [
                    'Stable Angina',
                    'Unstable Angina',
                    'Myocardial Ischemia',
                    'Costochondritis',
                    'GERD'
                ],
                'workup': [
                    'ECG',
                    'Cardiac Enzymes',
                    'Stress Test',
                    'Coronary CT Angiography'
                ],
                'guidelines': [
                    'ACC/AHA Chest Pain Guidelines',
                    'ESC Guidelines for Chronic Coronary Syndromes'
                ]
            },
            'fatigue': {
                'diagnoses': [
                    'Cardiovascular Disease',
                    'Anemia',
                    'Depression',
                    'Sleep Apnea',
                    'Hypothyroidism'
                ],
                'workup': [
                    'CBC',
                    'TSH',
                    'Basic Metabolic Panel',
                    'Sleep Study'
                ],
                'guidelines': [
                    'ACP Fatigue Workup Guidelines',
                    'NICE Chronic Fatigue Guidelines'
                ]
            },
            'hypertension': {
                'diagnoses': [
                    'Essential Hypertension',
                    'Secondary Hypertension',
                    'White Coat Hypertension',
                    'Resistant Hypertension'
                ],
                'workup': [
                    'Basic Metabolic Panel',
                    'Lipid Panel',
                    'Urinalysis',
                    'ECG',
                    'Ambulatory BP Monitoring'
                ],
                'guidelines': [
                    'ACC/AHA Hypertension Guidelines',
                    'ESC/ESH Guidelines for Hypertension',
                    'JNC 8 Guidelines'
                ]
            }
        }
        
        self.medication_classes = {
            'hypertension': [
                {'class': 'ACE Inhibitors', 'examples': ['lisinopril', 'ramipril']},
                {'class': 'ARBs', 'examples': ['losartan', 'valsartan']},
                {'class': 'CCBs', 'examples': ['amlodipine', 'diltiazem']},
                {'class': 'Thiazides', 'examples': ['hydrochlorothiazide', 'chlorthalidone']}
            ],
            'angina': [
                {'class': 'Beta Blockers', 'examples': ['metoprolol', 'carvedilol']},
                {'class': 'Nitrates', 'examples': ['nitroglycerin', 'isosorbide']},
                {'class': 'CCBs', 'examples': ['amlodipine', 'diltiazem']},
                {'class': 'Antiplatelet', 'examples': ['aspirin', 'clopidogrel']}
            ]
        }

    def parse_soap_note(self, text: str) -> SOAPNote:
        """Parse SOAP note text into structured format"""
        sections = self._split_into_sections(text)
        
        # Extract patient info
        patient_info = self._extract_patient_info(sections.get('header', ''))
        
        # Parse vital signs
        vitals = self._parse_vital_signs(sections.get('O', ''))
        
        # Parse assessment and plan
        assessment = self._parse_assessment(sections.get('A', ''))
        plan = self._parse_plan(sections.get('P', ''))
        
        return SOAPNote(
            patient_name=patient_info.get('name', ''),
            age=int(patient_info.get('age', 0)),
            date=datetime.strptime(patient_info.get('date', ''), '%Y-%m-%d'),
            provider=patient_info.get('provider', ''),
            visit_type=patient_info.get('visit_type', ''),
            subjective=sections.get('S', ''),
            objective={'vital_signs': vitals, 'exam': sections.get('O', '')},
            assessment=assessment,
            plan=plan,
            vital_signs=vitals
        )

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split SOAP note into sections"""
        sections = {}
        current_section = 'header'
        current_text = []
        
        for line in text.split('\n'):
            if line.strip().startswith('S –'):
                current_section = 'S'
                current_text = []
            elif line.strip().startswith('O –'):
                sections[current_section] = '\n'.join(current_text)
                current_section = 'O'
                current_text = []
            elif line.strip().startswith('A –'):
                sections[current_section] = '\n'.join(current_text)
                current_section = 'A'
                current_text = []
            elif line.strip().startswith('P –'):
                sections[current_section] = '\n'.join(current_text)
                current_section = 'P'
                current_text = []
            else:
                current_text.append(line.strip())
        
        sections[current_section] = '\n'.join(current_text)
        return sections

    def _extract_patient_info(self, header: str) -> Dict[str, str]:
        """Extract patient information from header"""
        info = {}
        lines = header.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip().lower().replace(' ', '_')] = value.strip()
        return info

    def _parse_vital_signs(self, objective: str) -> VitalSigns:
        """Parse vital signs from objective section"""
        vitals = VitalSigns()
        
        # Extract vital signs using regex
        bp_match = re.search(r'BP:\s*(\d+/\d+)', objective)
        if bp_match:
            vitals.blood_pressure = bp_match.group(1)
            
        hr_match = re.search(r'HR:\s*(\d+)', objective)
        if hr_match:
            vitals.heart_rate = hr_match.group(1)
            
        temp_match = re.search(r'Temp:\s*([\d.]+)', objective)
        if temp_match:
            vitals.temperature = temp_match.group(1)
            
        rr_match = re.search(r'RR:\s*(\d+)', objective)
        if rr_match:
            vitals.respiratory_rate = rr_match.group(1)
            
        spo2_match = re.search(r'SpO₂:\s*(\d+%)', objective)
        if spo2_match:
            vitals.oxygen_saturation = spo2_match.group(1)
            
        return vitals

    def _parse_assessment(self, assessment: str) -> List[str]:
        """Parse assessment section into list of problems"""
        problems = []
        for line in assessment.split('\n'):
            if '–' in line or '-' in line:
                continue
            if line.strip():
                problems.append(line.strip())
        return problems

    def _parse_plan(self, plan: str) -> Dict[str, List[str]]:
        """Parse plan section into categorized actions"""
        categories = {
            'Diagnostics': [],
            'Medications': [],
            'Lifestyle': [],
            'Follow-Up': []
        }
        
        current_category = None
        for line in plan.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.endswith(':'):
                current_category = line[:-1]
                continue
                
            if current_category and line.startswith('-'):
                categories[current_category].append(line[1:].strip())
                
        return categories

    def generate_search_queries(self, soap_note: SOAPNote) -> List[Dict[str, Any]]:
        """Generate targeted search queries based on SOAP note content"""
        queries = []
        
        # Extract symptoms and conditions
        symptoms = self._extract_symptoms(soap_note.subjective)
        conditions = soap_note.assessment
        bp_category = soap_note.vital_signs.get_bp_category()
        
        # Generate guideline-specific queries
        for condition in conditions:
            for guideline_type, sources in ClinicalGuidelines.GUIDELINE_SOURCES.items():
                for source in sources:
                    if any(keyword in condition.lower() for keyword in [source['topic'].lower()]):
                        queries.append({
                            'text': f"{source['org']} {source['topic']} guidelines {source['year']} recommendations",
                            'focus': 'clinical_guidelines',
                            'priority': 'high'
                        })

        # Generate risk assessment queries
        if any('cardiovascular' in s.lower() for s in symptoms + conditions):
            for calc in ClinicalGuidelines.RISK_CALCULATORS['cardiovascular']:
                queries.append({
                    'text': f"using {calc} for cardiovascular risk assessment",
                    'focus': 'risk_assessment',
                    'priority': 'medium'
                })

        # Generate medication-specific queries
        if 'Medications' in soap_note.plan:
            current_meds = soap_note.plan['Medications']
            for med in current_meds:
                queries.append({
                    'text': f"safety and efficacy of {med} in {bp_category.lower()} with {' and '.join(conditions)}",
                    'focus': 'medication',
                    'priority': 'high'
                })

        # Generate diagnostic queries
        for symptom in symptoms:
            if symptom in self.common_symptoms:
                for workup in self.common_symptoms[symptom]['workup']:
                    queries.append({
                        'text': f"evidence based approach to {workup} in {symptom}",
                        'focus': 'diagnostic',
                        'priority': 'medium'
                    })

        return queries

    def generate_recommendations(self, soap_note: SOAPNote) -> Dict[str, Any]:
        """Generate comprehensive clinical recommendations based on SOAP note analysis"""
        recommendations = {
            'urgent_actions': [],
            'risk_assessment': [],
            'diagnostics': [],
            'medications': [],
            'lifestyle': [],
            'monitoring': [],
            'referrals': [],
            'patient_education': [],
            'follow_up': [],
            'evidence_needed': []
        }
        
        # Check vital signs and generate urgent actions
        bp_category = soap_note.vital_signs.get_bp_category()
        if bp_category in ["Stage 2 Hypertension", "Hypertensive Crisis"]:
            recommendations['urgent_actions'].append({
                'action': f"Address {bp_category}",
                'rationale': f"BP indicates {bp_category}",
                'guideline': "ACC/AHA Hypertension Guidelines",
                'evidence_level': "Class I"
            })

        # Extract symptoms and check for red flags
        symptoms = self._extract_symptoms(soap_note.subjective)
        for symptom in symptoms:
            if symptom == 'chest_pain':
                for red_flag in ClinicalGuidelines.RED_FLAGS['chest_pain']:
                    if red_flag.lower() in soap_note.subjective.lower():
                        recommendations['urgent_actions'].append({
                            'action': f"Evaluate for acute coronary syndrome",
                            'rationale': f"Presence of red flag: {red_flag}",
                            'guideline': "ACC/AHA Chest Pain Guidelines",
                            'evidence_level': "Class I"
                        })

        # Generate diagnostic recommendations
        for symptom in symptoms:
            if symptom in self.common_symptoms:
                for workup in self.common_symptoms[symptom]['workup']:
                    recommendations['diagnostics'].append({
                        'test': workup,
                        'rationale': f"Evaluate {symptom}",
                        'guideline': self.common_symptoms[symptom]['guidelines'][0],
                        'priority': 'high' if 'ECG' in workup or 'Cardiac' in workup else 'routine'
                    })

        # Medication recommendations
        current_meds = soap_note.plan.get('Medications', [])
        for condition in soap_note.assessment:
            condition_lower = condition.lower()
            for med_category, meds in self.medication_classes.items():
                if med_category in condition_lower:
                    for med_class in meds:
                        if not any(current_med in med_class['examples'] for current_med in current_meds):
                            recommendations['medications'].append({
                                'action': f"Consider {med_class['class']}",
                                'rationale': f"Standard therapy for {condition}",
                                'examples': med_class['examples'],
                                'guideline': f"Current {condition} Guidelines"
                            })

        # Monitoring recommendations
        if bp_category != "Normal":
            recommendations['monitoring'].append({
                'action': "Home BP monitoring",
                'frequency': "Twice daily",
                'duration': "2 weeks",
                'target': "<130/80 mmHg",
                'guideline': "ACC/AHA Hypertension Guidelines"
            })

        # Patient education
        recommendations['patient_education'].extend([
            {
                'topic': "Cardiovascular Risk Factors",
                'resources': ["ACC CardioSmart", "AHA Patient Information"],
                'key_points': [
                    "Importance of medication adherence",
                    "Lifestyle modifications",
                    "Recognition of warning symptoms"
                ]
            },
            {
                'topic': "Lifestyle Modifications",
                'resources': ["DASH Diet", "Physical Activity Guidelines"],
                'key_points': [
                    "Sodium restriction",
                    "Regular exercise",
                    "Stress management"
                ]
            }
        ])

        # Follow-up recommendations
        recommendations['follow_up'].extend([
            {
                'timing': "1 week",
                'purpose': "Review diagnostic results",
                'modality': "In-person"
            },
            {
                'timing': "3 months",
                'purpose': "Medication adjustment",
                'modality': "Telehealth if stable"
            }
        ])

        return recommendations

    def _extract_symptoms(self, subjective: str) -> List[str]:
        """Extract symptoms from subjective section with enhanced pattern matching"""
        symptoms = []
        
        # Define symptom patterns with variations
        symptom_patterns = {
            'chest pain': [
                r'chest\s+(?:pain|discomfort|tightness|pressure)',
                r'angina',
                r'chest\s+(?:heaviness|squeezing)'
            ],
            'fatigue': [
                r'(?:feeling\s+)?(?:tired|fatigued|exhausted)',
                r'low\s+energy',
                r'lethargy'
            ],
            'shortness of breath': [
                r'(?:short|difficulty)\s+(?:of|with)\s+breath',
                r'dyspnea',
                r'breathing\s+(?:difficulty|problem)'
            ],
            'hypertension': [
                r'(?:high|elevated)\s+blood\s+pressure',
                r'hypertension'
            ]
        }
        
        # Check each symptom pattern
        for symptom, patterns in symptom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, subjective.lower()):
                    symptoms.append(symptom)
                    break  # Found one pattern for this symptom, move to next symptom
        
        return symptoms 