"""
Management command to seed expertise categories, specializations, and test questions.
Run: python manage.py seed_expertise_data
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from annotators.models import (
    ExpertiseCategory,
    ExpertiseSpecialization,
    ExpertiseTestQuestion,
)


# Expertise hierarchy - categories with their specializations
EXPERTISE_DATA = {
    "Computer Vision": {
        "icon": "image",
        "template_folder": "computer-vision",
        "description": "Annotation tasks involving image and visual data analysis, including object detection, segmentation, and classification.",
        "specializations": [
            {
                "name": "Object Detection",
                "icon": "target",
                "template_folder": "object-detection-with-bounding-boxes",
                "description": "Drawing bounding boxes around objects in images",
                "passing_score": 75,
            },
            {
                "name": "Image Classification",
                "icon": "tag",
                "template_folder": "image-classification",
                "description": "Categorizing entire images into predefined classes",
                "passing_score": 80,
            },
            {
                "name": "Semantic Segmentation",
                "icon": "layers",
                "template_folder": "semantic-segmentation-with-masks",
                "description": "Pixel-level labeling of image regions",
                "passing_score": 70,
            },
            {
                "name": "Image Captioning",
                "icon": "message-square",
                "template_folder": "image-captioning",
                "description": "Writing descriptive captions for images",
                "passing_score": 75,
            },
            {
                "name": "OCR/Text Recognition",
                "icon": "type",
                "template_folder": "optical-character-recognition",
                "description": "Transcribing text from images",
                "passing_score": 85,
            },
            {
                "name": "Keypoint Detection",
                "icon": "crosshair",
                "template_folder": "keypoints",
                "description": "Marking specific points of interest (e.g., body pose, facial landmarks)",
                "passing_score": 75,
            },
        ],
    },
    "Medical Imaging": {
        "icon": "activity",
        "template_folder": "medical-imaging",
        "description": "Specialized annotation for medical images including X-rays, CT scans, MRI, and pathology slides.",
        "specializations": [
            {
                "name": "Chest X-Ray Analysis",
                "icon": "heart",
                "template_folder": "dicom-classification",
                "description": "Annotating chest radiographs for lung conditions, cardiac abnormalities",
                "passing_score": 80,
                "requires_certification": True,
                "certification_instructions": "Please upload proof of medical imaging certification or relevant healthcare background.",
            },
            {
                "name": "CT Scan Annotation",
                "icon": "circle",
                "template_folder": "dicom-3d",
                "description": "3D annotation of computed tomography scans",
                "passing_score": 80,
                "requires_certification": True,
            },
            {
                "name": "MRI Segmentation",
                "icon": "grid",
                "template_folder": "dicom-segmentation",
                "description": "Segmenting anatomical structures in MRI scans",
                "passing_score": 80,
                "requires_certification": True,
            },
            {
                "name": "Pathology Slides",
                "icon": "microscope",
                "template_folder": "dicom-bbox",
                "description": "Annotating histopathology and microscopy images",
                "passing_score": 85,
                "requires_certification": True,
            },
            {
                "name": "Dental Imaging",
                "icon": "smile",
                "template_folder": "dicom-keypoint",
                "description": "X-ray annotation for dental conditions",
                "passing_score": 80,
            },
        ],
    },
    "Natural Language Processing": {
        "icon": "file-text",
        "template_folder": "natural-language-processing",
        "description": "Text-based annotation tasks including entity recognition, sentiment analysis, and text classification.",
        "specializations": [
            {
                "name": "Named Entity Recognition",
                "icon": "user",
                "template_folder": "named-entity-recognition",
                "description": "Identifying and categorizing entities (people, places, organizations) in text",
                "passing_score": 75,
            },
            {
                "name": "Sentiment Analysis",
                "icon": "smile",
                "template_folder": "sentiment-analysis",
                "description": "Classifying text sentiment (positive, negative, neutral)",
                "passing_score": 80,
            },
            {
                "name": "Text Classification",
                "icon": "folder",
                "template_folder": "text-classification",
                "description": "Categorizing documents into predefined categories",
                "passing_score": 75,
            },
            {
                "name": "Relation Extraction",
                "icon": "link",
                "template_folder": "relation-extraction",
                "description": "Identifying relationships between entities in text",
                "passing_score": 70,
            },
            {
                "name": "Machine Translation QA",
                "icon": "globe",
                "template_folder": "translation-quality",
                "description": "Evaluating and correcting machine translations",
                "passing_score": 80,
            },
        ],
    },
    "Audio/Speech Processing": {
        "icon": "mic",
        "template_folder": "audio-speech-processing",
        "description": "Audio annotation tasks including transcription, speaker diarization, and sound classification.",
        "specializations": [
            {
                "name": "Audio Transcription",
                "icon": "headphones",
                "template_folder": "audio-transcription",
                "description": "Transcribing spoken audio to text",
                "passing_score": 85,
            },
            {
                "name": "Speaker Diarization",
                "icon": "users",
                "template_folder": "speaker-identification",
                "description": "Identifying and labeling different speakers in audio",
                "passing_score": 75,
            },
            {
                "name": "Sound Event Detection",
                "icon": "volume-2",
                "template_folder": "sound-classification",
                "description": "Classifying and timestamping audio events",
                "passing_score": 70,
            },
            {
                "name": "Music Annotation",
                "icon": "music",
                "template_folder": "music-annotation",
                "description": "Labeling musical elements (instruments, genres, tempo)",
                "passing_score": 75,
            },
        ],
    },
    "Video Annotation": {
        "icon": "video",
        "template_folder": "videos",
        "description": "Video-based annotation tasks including object tracking, action recognition, and temporal segmentation.",
        "specializations": [
            {
                "name": "Object Tracking",
                "icon": "crosshair",
                "template_folder": "video-object-tracking",
                "description": "Tracking objects across video frames",
                "passing_score": 75,
            },
            {
                "name": "Action Recognition",
                "icon": "activity",
                "template_folder": "action-recognition",
                "description": "Identifying and labeling human actions in video",
                "passing_score": 70,
            },
            {
                "name": "Temporal Segmentation",
                "icon": "clock",
                "template_folder": "video-segmentation",
                "description": "Marking time boundaries for events in video",
                "passing_score": 75,
            },
            {
                "name": "Video Captioning",
                "icon": "message-square",
                "template_folder": "video-captioning",
                "description": "Writing descriptions for video content",
                "passing_score": 75,
            },
        ],
    },
    "Conversational AI": {
        "icon": "message-circle",
        "template_folder": "conversational-ai",
        "description": "Annotation for chatbot training, dialog classification, and conversation quality assessment.",
        "specializations": [
            {
                "name": "Intent Classification",
                "icon": "target",
                "template_folder": "intent-classification",
                "description": "Classifying user intents in conversational data",
                "passing_score": 80,
            },
            {
                "name": "Dialog Act Tagging",
                "icon": "tag",
                "template_folder": "dialog-acts",
                "description": "Labeling dialog acts (questions, answers, commands)",
                "passing_score": 75,
            },
            {
                "name": "Response Quality Rating",
                "icon": "star",
                "template_folder": "response-rating",
                "description": "Rating chatbot response quality",
                "passing_score": 70,
            },
        ],
    },
    "Generative AI": {
        "icon": "zap",
        "template_folder": "generative-ai",
        "description": "Annotation for evaluating and improving generative AI outputs including text, images, and code.",
        "specializations": [
            {
                "name": "Text Generation QA",
                "icon": "edit",
                "template_folder": "text-generation-qa",
                "description": "Evaluating generated text quality and factual accuracy",
                "passing_score": 80,
            },
            {
                "name": "Image Generation Rating",
                "icon": "image",
                "template_folder": "image-generation-rating",
                "description": "Rating quality and adherence to prompts for AI-generated images",
                "passing_score": 75,
            },
            {
                "name": "Code Review",
                "icon": "code",
                "template_folder": "code-review",
                "description": "Evaluating AI-generated code for correctness and quality",
                "passing_score": 85,
            },
            {
                "name": "RLHF Preference Ranking",
                "icon": "thumbs-up",
                "template_folder": "preference-ranking",
                "description": "Ranking multiple AI outputs for RLHF training",
                "passing_score": 75,
            },
        ],
    },
    "Structured Data Parsing": {
        "icon": "database",
        "template_folder": "structured-data-parsing",
        "description": "Extracting structured information from documents, receipts, forms, and tables.",
        "specializations": [
            {
                "name": "Document Parsing",
                "icon": "file-text",
                "template_folder": "document-parsing",
                "description": "Extracting structured data from documents",
                "passing_score": 80,
            },
            {
                "name": "Receipt/Invoice Extraction",
                "icon": "receipt",
                "template_folder": "receipt-extraction",
                "description": "Parsing receipts and invoices for key fields",
                "passing_score": 85,
            },
            {
                "name": "Table Recognition",
                "icon": "table",
                "template_folder": "table-recognition",
                "description": "Extracting tabular data from images",
                "passing_score": 80,
            },
        ],
    },
}


# Sample test questions for each category
TEST_QUESTIONS = {
    "Computer Vision": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is a bounding box in object detection?",
            "options": [
                "A 3D representation of an object",
                "A rectangular region that encloses an object",
                "A pixel-level mask of an object",
                "A line connecting object centers",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "A bounding box is a rectangular region defined by coordinates that encloses the object of interest.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "Which annotation type is most suitable for counting objects in a crowded scene?",
            "options": [
                "Semantic segmentation",
                "Point annotations",
                "Image-level classification",
                "Image captioning",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Point annotations (one point per object) are efficient for counting in crowded scenes where bounding boxes would overlap significantly.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "What is the difference between semantic and instance segmentation?",
            "options": [
                "Semantic segmentation is faster",
                "Instance segmentation distinguishes between individual objects of the same class",
                "Semantic segmentation uses bounding boxes",
                "Instance segmentation only works with medical images",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Instance segmentation identifies each individual object separately, while semantic segmentation groups all pixels of the same class together.",
        },
        {
            "question_type": "mcq",
            "difficulty": "hard",
            "question_text": "When annotating partially occluded objects, what is the best practice?",
            "options": [
                "Skip the object entirely",
                "Only annotate the visible portion",
                "Annotate the full estimated extent of the object",
                "Mark it as 'unclear'",
            ],
            "correct_answer": 2,
            "points": 4,
            "explanation": "Best practice is to annotate the full estimated extent of the object, as this provides the most useful training data for models to learn about occluded objects.",
        },
        {
            "question_type": "true_false",
            "difficulty": "easy",
            "question_text": "In image classification, each image can only have one label.",
            "options": ["True", "False"],
            "correct_answer": 1,  # False
            "points": 2,
            "explanation": "This is false. Multi-label classification allows multiple labels per image.",
        },
    ],
    "Medical Imaging": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What does DICOM stand for?",
            "options": [
                "Digital Imaging and Communications in Medicine",
                "Digital Image Compression Method",
                "Diagnostic Imaging Computer Output Module",
                "Digital Integrated Clinical Output Management",
            ],
            "correct_answer": 0,
            "points": 2,
            "explanation": "DICOM stands for Digital Imaging and Communications in Medicine - the international standard for medical images.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "When annotating a chest X-ray, which anatomical structure appears brightest (most radiopaque)?",
            "options": [
                "Lungs",
                "Heart",
                "Bones (ribs, spine)",
                "Soft tissue",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "Bones appear brightest on X-rays because they are most radiopaque (block X-rays most effectively).",
        },
        {
            "question_type": "mcq",
            "difficulty": "hard",
            "question_text": "What is the Hounsfield Unit (HU) scale used for?",
            "options": [
                "Measuring image resolution in MRI",
                "Quantifying tissue density in CT scans",
                "Calibrating ultrasound machines",
                "Measuring magnetic field strength",
            ],
            "correct_answer": 1,
            "points": 4,
            "explanation": "Hounsfield Units are used in CT imaging to quantify radiodensity. Water is 0 HU, air is -1000 HU, and bone is typically +400 to +1000 HU.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "Why is patient de-identification important in medical image annotation?",
            "options": [
                "To reduce file size",
                "To improve image quality",
                "To protect patient privacy (HIPAA compliance)",
                "To enable faster processing",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "De-identification is crucial to protect patient privacy and comply with regulations like HIPAA.",
        },
    ],
    "Natural Language Processing": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is Named Entity Recognition (NER)?",
            "options": [
                "Translating text between languages",
                "Identifying entities like people, places, organizations in text",
                "Summarizing long documents",
                "Checking grammar and spelling",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "NER identifies and classifies named entities in text into predefined categories.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "In sentiment analysis, a text saying 'The product is not bad' should typically be classified as:",
            "options": [
                "Strongly negative",
                "Negative",
                "Neutral to slightly positive",
                "Strongly positive",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "'Not bad' is a litotes (understatement) that typically conveys slightly positive sentiment.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "What is tokenization in NLP?",
            "options": [
                "Encrypting text data",
                "Breaking text into smaller units (words, subwords, characters)",
                "Translating text to numbers",
                "Removing punctuation",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Tokenization splits text into tokens (words, subwords, or characters) for processing.",
        },
        {
            "question_type": "mcq",
            "difficulty": "hard",
            "question_text": "What is coreference resolution?",
            "options": [
                "Finding synonyms in text",
                "Linking pronouns and mentions to the entities they refer to",
                "Detecting duplicate sentences",
                "Measuring text similarity",
            ],
            "correct_answer": 1,
            "points": 4,
            "explanation": "Coreference resolution identifies when different expressions refer to the same entity (e.g., 'John' and 'he').",
        },
    ],
    "Audio/Speech Processing": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is speaker diarization?",
            "options": [
                "Converting speech to text",
                "Segmenting audio by who is speaking",
                "Removing background noise",
                "Adjusting audio volume",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "Speaker diarization segments audio to identify 'who spoke when'.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "When transcribing audio, how should unclear speech be handled?",
            "options": [
                "Skip it entirely",
                "Guess the most likely words",
                "Mark it with a convention like [inaudible] or [unclear]",
                "Replace with silence indicators",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "Standard practice is to mark unclear speech with conventions like [inaudible] rather than guessing.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "What information should timestamps in audio transcription typically include?",
            "options": [
                "Only start time",
                "Only end time",
                "Both start and end times",
                "Timestamps are not needed",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "Both start and end times are typically needed for accurate alignment and playback.",
        },
    ],
    "Video Annotation": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is temporally consistent annotation in video?",
            "options": [
                "Annotating every frame independently",
                "Ensuring annotations are consistent across frames for the same object",
                "Only annotating keyframes",
                "Using the same color for all annotations",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "Temporal consistency means the same object should have consistent IDs and labels across frames.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "What is interpolation in video annotation?",
            "options": [
                "Deleting annotations",
                "Automatically generating annotations between keyframes",
                "Converting video to images",
                "Changing annotation colors",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Interpolation automatically creates annotations for frames between manually annotated keyframes.",
        },
        {
            "question_type": "mcq",
            "difficulty": "hard",
            "question_text": "When should you create a new track ID for an object in video annotation?",
            "options": [
                "Every time the object moves",
                "When the object is temporarily occluded",
                "When the object leaves and re-enters the scene",
                "At regular intervals",
            ],
            "correct_answer": 2,
            "points": 4,
            "explanation": "A new track ID is typically created when an object completely leaves the scene and returns, as continuity cannot be guaranteed.",
        },
    ],
    "Conversational AI": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is intent classification in conversational AI?",
            "options": [
                "Measuring conversation length",
                "Identifying what the user wants to accomplish",
                "Counting words in messages",
                "Detecting language type",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "Intent classification identifies the user's goal (e.g., book a flight, check weather).",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "What are slot values in a dialog system?",
            "options": [
                "The timing of responses",
                "Specific pieces of information needed to fulfill an intent",
                "The number of turns in a conversation",
                "Error messages",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Slots are the specific parameters needed (e.g., for 'book flight': departure_city, arrival_city, date).",
        },
    ],
    "Generative AI": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is RLHF in the context of AI training?",
            "options": [
                "Random Learning from Hardware",
                "Reinforcement Learning from Human Feedback",
                "Recursive Language Handling Framework",
                "Real-time Learning for Hardware",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "RLHF uses human preferences to fine-tune AI models.",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "When evaluating AI-generated text, which of these is NOT typically a quality criterion?",
            "options": [
                "Factual accuracy",
                "Coherence and fluency",
                "Processing speed",
                "Relevance to prompt",
            ],
            "correct_answer": 2,
            "points": 3,
            "explanation": "Processing speed is a system metric, not a text quality criterion.",
        },
        {
            "question_type": "mcq",
            "difficulty": "hard",
            "question_text": "In preference ranking for RLHF, why is it important to have consistent criteria?",
            "options": [
                "To make annotation faster",
                "To reduce the number of comparisons needed",
                "To ensure the model learns coherent preferences without conflicting signals",
                "To minimize storage requirements",
            ],
            "correct_answer": 2,
            "points": 4,
            "explanation": "Consistent criteria prevent contradictory training signals that could confuse the model.",
        },
    ],
    "Structured Data Parsing": [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "question_text": "What is a key-value pair in document parsing?",
            "options": [
                "A password and username combination",
                "A field name paired with its content (e.g., 'Date: 01/01/2024')",
                "A row in a spreadsheet",
                "An image and its caption",
            ],
            "correct_answer": 1,
            "points": 2,
            "explanation": "Key-value pairs consist of a label (key) and its associated data (value).",
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "question_text": "When parsing a receipt, which fields are typically most important to extract?",
            "options": [
                "Store logo and colors",
                "Total amount, date, items, and payment method",
                "Font type and size",
                "Paper dimensions",
            ],
            "correct_answer": 1,
            "points": 3,
            "explanation": "Key fields for receipts include total, date, line items, and payment method.",
        },
    ],
}


class Command(BaseCommand):
    help = "Seed expertise categories, specializations, and test questions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing expertise data...")
            ExpertiseTestQuestion.objects.all().delete()
            ExpertiseSpecialization.objects.all().delete()
            ExpertiseCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing data cleared."))

        self.stdout.write("Seeding expertise data...")

        # Create categories and specializations
        order = 0
        for cat_name, cat_data in EXPERTISE_DATA.items():
            category, created = ExpertiseCategory.objects.update_or_create(
                name=cat_name,
                defaults={
                    "slug": slugify(cat_name),
                    "description": cat_data.get("description", ""),
                    "icon": cat_data.get("icon", ""),
                    "template_folder": cat_data.get("template_folder", ""),
                    "display_order": order,
                    "is_active": True,
                },
            )
            order += 1

            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} category: {cat_name}")

            # Create specializations
            spec_order = 0
            for spec_data in cat_data.get("specializations", []):
                spec, spec_created = ExpertiseSpecialization.objects.update_or_create(
                    category=category,
                    name=spec_data["name"],
                    defaults={
                        "slug": slugify(spec_data["name"]),
                        "description": spec_data.get("description", ""),
                        "icon": spec_data.get("icon", ""),
                        "template_folder": spec_data.get("template_folder", ""),
                        "requires_certification": spec_data.get(
                            "requires_certification", False
                        ),
                        "certification_instructions": spec_data.get(
                            "certification_instructions", ""
                        ),
                        "passing_score": spec_data.get("passing_score", 70),
                        "display_order": spec_order,
                        "is_active": True,
                    },
                )
                spec_order += 1

                action = "Created" if spec_created else "Updated"
                self.stdout.write(f"    {action} specialization: {spec_data['name']}")

        # Create test questions
        self.stdout.write("\nSeeding test questions...")
        for cat_name, questions in TEST_QUESTIONS.items():
            try:
                category = ExpertiseCategory.objects.get(name=cat_name)
            except ExpertiseCategory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  Category not found: {cat_name}")
                )
                continue

            for q_data in questions:
                question, q_created = ExpertiseTestQuestion.objects.update_or_create(
                    category=category,
                    question_text=q_data["question_text"],
                    defaults={
                        "question_type": q_data.get("question_type", "mcq"),
                        "difficulty": q_data.get("difficulty", "medium"),
                        "options": q_data.get("options", []),
                        "correct_answer": q_data.get("correct_answer"),
                        "points": q_data.get("points", 1),
                        "explanation": q_data.get("explanation", ""),
                        "is_active": True,
                    },
                )

            self.stdout.write(f"  Added {len(questions)} questions for {cat_name}")

        self.stdout.write(self.style.SUCCESS("\nExpertise data seeded successfully!"))

        # Summary
        cat_count = ExpertiseCategory.objects.count()
        spec_count = ExpertiseSpecialization.objects.count()
        q_count = ExpertiseTestQuestion.objects.count()
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"  Categories: {cat_count}")
        self.stdout.write(f"  Specializations: {spec_count}")
        self.stdout.write(f"  Test Questions: {q_count}")
