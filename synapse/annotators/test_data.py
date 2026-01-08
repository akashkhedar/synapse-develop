"""Test questions and tasks for annotator qualification"""

# Medical Knowledge Questions
MEDICAL_KNOWLEDGE_QUESTIONS = [
    {
        "id": 1,
        "type": "mcq",
        "question": "What does MRI stand for?",
        "options": [
            "Magnetic Resonance Imaging",
            "Medical Radiology Imaging",
            "Magnetic Radiation Imaging",
            "Medical Resonance Instrument"
        ],
        "correct_answer": 0,
        "points": 2
    },
    {
        "id": 2,
        "type": "mcq",
        "question": "Which of the following is NOT a vital sign?",
        "options": [
            "Blood Pressure",
            "Heart Rate",
            "Temperature",
            "Blood Type"
        ],
        "correct_answer": 3,
        "points": 2
    },
    {
        "id": 3,
        "type": "mcq",
        "question": "What does HIPAA primarily regulate?",
        "options": [
            "Hospital staffing requirements",
            "Patient data privacy and security",
            "Medical device safety",
            "Pharmaceutical pricing"
        ],
        "correct_answer": 1,
        "points": 3
    },
    {
        "id": 4,
        "type": "mcq",
        "question": "In medical terminology, what does the prefix 'hyper-' mean?",
        "options": [
            "Below normal",
            "Above normal",
            "Without",
            "Within"
        ],
        "correct_answer": 1,
        "points": 2
    },
    {
        "id": 5,
        "type": "mcq",
        "question": "Which imaging technique uses ionizing radiation?",
        "options": [
            "MRI",
            "Ultrasound",
            "X-Ray",
            "PET Scan (only option C)"
        ],
        "correct_answer": 2,
        "points": 2
    },
    {
        "id": 6,
        "type": "mcq",
        "question": "What does 'NPO' mean in medical instructions?",
        "options": [
            "No pain observed",
            "Nothing by mouth",
            "Normal patient outcome",
            "New prescription ordered"
        ],
        "correct_answer": 1,
        "points": 2
    },
    {
        "id": 7,
        "type": "mcq",
        "question": "Which organ is primarily affected in hepatitis?",
        "options": [
            "Heart",
            "Liver",
            "Kidneys",
            "Lungs"
        ],
        "correct_answer": 1,
        "points": 2
    },
    {
        "id": 8,
        "type": "mcq",
        "question": "What is the normal range for adult resting heart rate (bpm)?",
        "options": [
            "40-60",
            "60-100",
            "100-140",
            "140-180"
        ],
        "correct_answer": 1,
        "points": 2
    },
    {
        "id": 9,
        "type": "mcq",
        "question": "What does NER stand for in medical text annotation?",
        "options": [
            "Numeric Entity Recognition",
            "Named Entity Recognition",
            "Neural Entity Relation",
            "Normalized Entry Recording"
        ],
        "correct_answer": 1,
        "points": 3
    },
    {
        "id": 10,
        "type": "mcq",
        "question": "Which of these is a common medical abbreviation for 'twice a day'?",
        "options": [
            "QD",
            "BID",
            "TID",
            "QID"
        ],
        "correct_answer": 1,
        "points": 2
    }
]

# Text Annotation Tasks (NER)
TEXT_ANNOTATION_TASKS = [
    {
        "id": 1,
        "type": "ner",
        "instruction": "Identify and label all MEDICATIONS, DISEASES, and SYMPTOMS in the following clinical note.",
        "text": "Patient presents with hypertension and diabetes mellitus. Prescribed Lisinopril 10mg daily and Metformin 500mg twice daily. Reports frequent headaches and fatigue.",
        "labels": ["MEDICATION", "DISEASE", "SYMPTOM"],
        "ground_truth": [
            {"start": 22, "end": 34, "text": "hypertension", "label": "DISEASE"},
            {"start": 39, "end": 56, "text": "diabetes mellitus", "label": "DISEASE"},
            {"start": 69, "end": 79, "text": "Lisinopril", "label": "MEDICATION"},
            {"start": 99, "end": 108, "text": "Metformin", "label": "MEDICATION"},
            {"start": 144, "end": 153, "text": "headaches", "label": "SYMPTOM"},
            {"start": 158, "end": 165, "text": "fatigue", "label": "SYMPTOM"}
        ],
        "points": 15
    },
    {
        "id": 2,
        "type": "ner",
        "instruction": "Identify and label all MEDICATIONS and DOSAGES in the following prescription.",
        "text": "Rx: Aspirin 100mg once daily, Atorvastatin 20mg at bedtime, Omeprazole 40mg before breakfast.",
        "labels": ["MEDICATION", "DOSAGE"],
        "ground_truth": [
            {"start": 4, "end": 11, "text": "Aspirin", "label": "MEDICATION"},
            {"start": 12, "end": 17, "text": "100mg", "label": "DOSAGE"},
            {"start": 30, "end": 42, "text": "Atorvastatin", "label": "MEDICATION"},
            {"start": 43, "end": 47, "text": "20mg", "label": "DOSAGE"},
            {"start": 61, "end": 71, "text": "Omeprazole", "label": "MEDICATION"},
            {"start": 72, "end": 76, "text": "40mg", "label": "DOSAGE"}
        ],
        "points": 15
    },
    {
        "id": 3,
        "type": "ner",
        "instruction": "Identify and label all anatomical LOCATIONS and PROCEDURES mentioned.",
        "text": "CT scan of the chest revealed a mass in the right upper lobe. Bronchoscopy with biopsy scheduled for next week.",
        "labels": ["LOCATION", "PROCEDURE"],
        "ground_truth": [
            {"start": 0, "end": 7, "text": "CT scan", "label": "PROCEDURE"},
            {"start": 15, "end": 20, "text": "chest", "label": "LOCATION"},
            {"start": 44, "end": 60, "text": "right upper lobe", "label": "LOCATION"},
            {"start": 62, "end": 74, "text": "Bronchoscopy", "label": "PROCEDURE"},
            {"start": 80, "end": 86, "text": "biopsy", "label": "PROCEDURE"}
        ],
        "points": 15
    }
]

# Classification Tasks
CLASSIFICATION_TASKS = [
    {
        "id": 1,
        "type": "classification",
        "instruction": "Classify the urgency level of this patient case.",
        "text": "45-year-old male with sudden onset severe chest pain radiating to left arm, diaphoresis, and shortness of breath. Onset 30 minutes ago.",
        "options": ["Routine", "Urgent", "Emergency", "Non-urgent"],
        "correct_answer": 2,
        "points": 10,
        "explanation": "This presents classic symptoms of acute myocardial infarction (heart attack) requiring immediate emergency care."
    },
    {
        "id": 2,
        "type": "classification",
        "instruction": "Classify the type of medical report.",
        "text": "IMPRESSION: No acute cardiopulmonary process. Heart size normal. Lungs clear. No pleural effusion or pneumothorax.",
        "options": ["Lab Report", "Chest X-Ray Report", "MRI Report", "Pathology Report"],
        "correct_answer": 1,
        "points": 10,
        "explanation": "Language indicates radiological imaging of chest with assessment of cardiopulmonary structures."
    },
    {
        "id": 3,
        "type": "classification",
        "instruction": "Identify the medical specialty most relevant to this case.",
        "text": "Patient with recurrent seizures, loss of consciousness, and abnormal EEG findings. Family history of epilepsy.",
        "options": ["Cardiology", "Neurology", "Gastroenterology", "Orthopedics"],
        "correct_answer": 1,
        "points": 10,
        "explanation": "Seizures and EEG abnormalities are neurological conditions."
    }
]

# Scoring thresholds
SCORING_CONFIG = {
    "knowledge_total": 22,  # Total points for MCQs
    "text_annotation_total": 45,  # Total points for NER tasks
    "classification_total": 30,  # Total points for classification
    "total_points": 97,
    
    "pass_threshold": 68,  # 70% overall
    "knowledge_min": 13,  # 60% of knowledge
    "practical_min": 53,  # 70% of practical (text + classification)
    
    "time_limit_minutes": 60
}

def get_full_test():
    """Get complete test data"""
    return {
        "knowledge_questions": MEDICAL_KNOWLEDGE_QUESTIONS,
        "text_annotation_tasks": TEXT_ANNOTATION_TASKS,
        "classification_tasks": CLASSIFICATION_TASKS,
        "scoring_config": SCORING_CONFIG
    }





