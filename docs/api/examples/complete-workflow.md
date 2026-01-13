# Complete Workflow Examples

Real-world examples showing end-to-end annotation workflows.

## Table of Contents

- [Image Classification Pipeline](#image-classification-pipeline)
- [Object Detection for YOLO Training](#object-detection-for-yolo-training)
- [Named Entity Recognition (NER)](#named-entity-recognition-ner)
- [Video Annotation Pipeline](#video-annotation-pipeline)
- [Async Workflow with Webhooks](#async-workflow-with-webhooks)
- [High-Volume Production Pipeline](#high-volume-production-pipeline)

---

## Image Classification Pipeline

Complete example: Train an image classifier with human-labeled data.

```python
import synapse
import json
from pathlib import Path

# Initialize client
client = synapse.Client(api_key="sk_live_xxxx")

# =============================================================================
# STEP 1: Create Project
# =============================================================================
project = client.projects.create(
    name="Product Image Classification",
    annotation_type="classification",
    data_type="image",
    labels=[
        "Electronics",
        "Clothing", 
        "Home & Kitchen",
        "Sports & Outdoors",
        "Books",
        "Toys & Games",
        "Other"
    ],
    instructions="""
    Classify each product image into the most appropriate category.
    
    Guidelines:
    - Choose the single best category
    - If a product could fit multiple categories, choose the primary use
    - Use "Other" only if none of the categories apply
    """,
    quality_settings={
        "min_annotators": 3,
        "consensus_threshold": 0.66,
        "honeypot_percentage": 5
    },
    pricing_tier="standard"
)

print(f"Created project: {project.id}")

# =============================================================================
# STEP 2: Upload Data from S3
# =============================================================================
result = project.upload_from_s3(
    bucket="my-product-images",
    prefix="catalog/2025/",
    file_types=["jpg", "png", "webp"]
)

print(f"Uploaded {result.task_count} images")

# =============================================================================
# STEP 3: Calculate and Pay Deposit
# =============================================================================
deposit = project.calculate_deposit()
print(f"Deposit required: {deposit.currency} {deposit.amount}")
print(f"Breakdown:")
print(f"  - Annotation cost: {deposit.breakdown['annotation_cost']}")
print(f"  - Quality assurance: {deposit.breakdown['quality_assurance']}")
print(f"  - Platform fee: {deposit.breakdown['platform_fee']}")

# Pay with account credits
payment = project.pay_deposit(payment_method="credits")
print(f"Payment successful: {payment.id}")

# =============================================================================
# STEP 4: Monitor Progress
# =============================================================================
import time

while not project.is_complete():
    status = project.get_status()
    print(f"Progress: {status.progress:.1f}% ({status.completed_tasks}/{status.total_tasks})")
    print(f"  - Quality score: {status.quality_metrics['average_agreement']:.2%}")
    print(f"  - Est. completion: {status.estimated_completion}")
    time.sleep(300)  # Check every 5 minutes

print("Project complete!")

# =============================================================================
# STEP 5: Export Annotations
# =============================================================================
annotations = project.export(format="json")

# Save to file
with open("annotations.json", "w") as f:
    json.dump(annotations, f, indent=2)

print(f"Exported {len(annotations)} annotations")

# =============================================================================
# STEP 6: Prepare for Training
# =============================================================================
from sklearn.model_selection import train_test_split

# Convert to training format
data = []
for annotation in annotations:
    data.append({
        "image_path": annotation["task"]["data"]["image_url"],
        "label": annotation["result"]["classification"]["label"],
        "confidence": annotation["result"]["classification"]["confidence"]
    })

# Split into train/val/test
train_data, temp_data = train_test_split(data, test_size=0.3, random_state=42)
val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

print(f"Training set: {len(train_data)}")
print(f"Validation set: {len(val_data)}")
print(f"Test set: {len(test_data)}")
```

---

## Object Detection for YOLO Training

Complete pipeline for training YOLOv8 with Synapse annotations.

```python
import synapse
from pathlib import Path
import yaml

client = synapse.Client(api_key="sk_live_xxxx")

# =============================================================================
# STEP 1: Create Object Detection Project
# =============================================================================
project = client.projects.create(
    name="Vehicle Detection Dataset",
    annotation_type="bounding_box",
    data_type="image",
    labels=[
        "car",
        "truck", 
        "motorcycle",
        "bicycle",
        "bus",
        "pedestrian"
    ],
    instructions="""
    Draw tight bounding boxes around all vehicles and pedestrians.
    
    Rules:
    - Include partially visible objects (if >30% visible)
    - Draw separate boxes for overlapping objects
    - Include reflections in mirrors only if clearly identifiable
    - Skip objects that are too small (<10px in any dimension)
    """,
    quality_settings={
        "min_annotators": 3,
        "consensus_threshold": 0.7,
        "enable_expert_review": True,
        "iou_threshold": 0.5  # For bounding box consensus
    },
    pricing_tier="premium",
    priority="high"
)

# =============================================================================
# STEP 2: Upload Training Images
# =============================================================================
# Option A: From S3
result = project.upload_from_s3(
    bucket="autonomous-driving-data",
    prefix="frames/highway/",
    file_types=["jpg", "png"]
)

# Option B: From local files (if needed)
# tasks = [
#     {"image_url": f"https://cdn.example.com/images/{i}.jpg"}
#     for i in range(10000)
# ]
# result = project.upload_tasks(tasks)

print(f"Uploaded {result.task_count} images")

# =============================================================================
# STEP 3: Pay and Start
# =============================================================================
deposit = project.calculate_deposit()
project.pay_deposit(payment_method="credits")

# Wait for completion with progress callback
def progress_callback(status):
    print(f"[{status.progress:.1f}%] {status.completed_tasks}/{status.total_tasks} tasks")
    print(f"  IoU score: {status.quality_metrics.get('average_iou', 'N/A')}")

project.wait_for_completion(poll_interval=600, callback=progress_callback)

# =============================================================================
# STEP 4: Export in YOLO Format
# =============================================================================
yolo_export = project.export(format="yolo")

# Structure returned:
# {
#     "images_dir": "/tmp/synapse_export_xxx/images/",
#     "labels_dir": "/tmp/synapse_export_xxx/labels/",
#     "classes": ["car", "truck", "motorcycle", "bicycle", "bus", "pedestrian"],
#     "data_yaml": {...}
# }

# Create YOLO dataset structure
output_dir = Path("datasets/vehicle_detection")
output_dir.mkdir(parents=True, exist_ok=True)

# Move files to proper structure
import shutil
shutil.copytree(yolo_export["images_dir"], output_dir / "images")
shutil.copytree(yolo_export["labels_dir"], output_dir / "labels")

# Create data.yaml for YOLOv8
data_yaml = {
    "path": str(output_dir.absolute()),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "names": {i: name for i, name in enumerate(yolo_export["classes"])}
}

with open(output_dir / "data.yaml", "w") as f:
    yaml.dump(data_yaml, f)

# =============================================================================
# STEP 5: Train YOLOv8
# =============================================================================
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # Load pretrained model

results = model.train(
    data=str(output_dir / "data.yaml"),
    epochs=100,
    imgsz=640,
    batch=16,
    device=0
)

print(f"Training complete! mAP50: {results.results_dict['metrics/mAP50(B)']:.3f}")
```

---

## Named Entity Recognition (NER)

Build an NER model with human-annotated text data.

```python
import synapse
import json

client = synapse.Client(api_key="sk_live_xxxx")

# =============================================================================
# STEP 1: Create NER Project
# =============================================================================
project = client.projects.create(
    name="Legal Document NER",
    annotation_type="ner",
    data_type="text",
    labels=[
        "PERSON",
        "ORGANIZATION",
        "DATE",
        "MONEY",
        "LOCATION",
        "CASE_NUMBER",
        "COURT",
        "STATUTE"
    ],
    instructions="""
    Identify and label named entities in legal documents.
    
    Entity Types:
    - PERSON: Names of individuals (parties, judges, lawyers)
    - ORGANIZATION: Companies, government bodies, law firms
    - DATE: Dates and time periods
    - MONEY: Monetary amounts
    - LOCATION: Addresses, cities, jurisdictions
    - CASE_NUMBER: Case/docket numbers
    - COURT: Court names
    - STATUTE: Law references (e.g., "18 U.S.C. § 1341")
    
    Guidelines:
    - Include titles with names (e.g., "Judge Smith")
    - Don't include generic references (e.g., "the defendant")
    - Mark partial dates if that's all that's present
    """,
    quality_settings={
        "min_annotators": 2,
        "consensus_threshold": 0.8,
        "enable_expert_review": True
    }
)

# =============================================================================
# STEP 2: Upload Text Documents
# =============================================================================
# Load documents from your data source
documents = [
    {
        "text": """On January 15, 2024, in the United States District Court 
        for the Southern District of New York, Case No. 1:24-cv-00123, 
        Judge Sarah Thompson ruled that Acme Corporation must pay 
        $2.5 million in damages to John Smith...""",
        "metadata": {"source": "court_filing", "doc_id": "doc_001"}
    },
    # ... more documents
]

result = project.upload_tasks(documents)
print(f"Uploaded {result.task_count} documents")

# =============================================================================
# STEP 3: Pay and Monitor
# =============================================================================
project.pay_deposit(payment_method="credits")
project.wait_for_completion()

# =============================================================================
# STEP 4: Export in spaCy Format
# =============================================================================
spacy_data = project.export(format="spacy")

# Save training data
with open("ner_training_data.spacy", "wb") as f:
    f.write(spacy_data)

# Or get as JSON for custom processing
json_data = project.export(format="json")

# Convert to spaCy training format manually if needed
training_data = []
for item in json_data:
    text = item["task"]["data"]["text"]
    entities = []
    for entity in item["result"]["entities"]:
        entities.append((
            entity["start"],
            entity["end"],
            entity["label"]
        ))
    training_data.append((text, {"entities": entities}))

# =============================================================================
# STEP 5: Train spaCy Model
# =============================================================================
import spacy
from spacy.training import Example

nlp = spacy.blank("en")
ner = nlp.add_pipe("ner")

# Add labels
for label in ["PERSON", "ORGANIZATION", "DATE", "MONEY", "LOCATION", 
              "CASE_NUMBER", "COURT", "STATUTE"]:
    ner.add_label(label)

# Train
optimizer = nlp.begin_training()
for epoch in range(30):
    losses = {}
    for text, annotations in training_data:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        nlp.update([example], losses=losses, sgd=optimizer)
    print(f"Epoch {epoch}: {losses}")

nlp.to_disk("legal_ner_model")
```

---

## Video Annotation Pipeline

Annotate video data for action recognition or tracking.

```python
import synapse

client = synapse.Client(api_key="sk_live_xxxx")

# =============================================================================
# STEP 1: Create Video Annotation Project
# =============================================================================
project = client.projects.create(
    name="Sports Action Recognition",
    annotation_type=["classification", "keypoint"],
    data_type="video",
    labels={
        "classification": [
            "running", "jumping", "throwing", "catching",
            "kicking", "hitting", "swimming", "climbing"
        ],
        "keypoint": [
            "head", "neck", "left_shoulder", "right_shoulder",
            "left_elbow", "right_elbow", "left_wrist", "right_wrist",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle"
        ]
    },
    instructions="""
    For each video clip:
    1. Classify the primary action being performed
    2. Mark keypoints on the athlete's body in key frames
    
    Keypoint marking:
    - Mark keypoints every 10 frames (or at action transitions)
    - Mark all visible keypoints
    - Use "occluded" flag for partially visible joints
    """,
    quality_settings={
        "min_annotators": 2,
        "frame_sampling_rate": 10  # Annotate every 10th frame
    },
    pricing_tier="premium"  # Video annotation costs more
)

# =============================================================================
# STEP 2: Upload Videos
# =============================================================================
result = project.upload_from_s3(
    bucket="sports-videos",
    prefix="clips/basketball/",
    file_types=["mp4", "avi", "mov"]
)

# =============================================================================
# STEP 3: Complete workflow
# =============================================================================
project.pay_deposit(payment_method="credits")
project.wait_for_completion()

# Export in JSON format for video annotations
annotations = project.export(format="json")

# Structure for video annotations:
# {
#     "video_url": "...",
#     "duration": 10.5,
#     "fps": 30,
#     "classification": {"label": "jumping", "confidence": 0.95},
#     "keypoints": {
#         "frame_0": {...keypoint data...},
#         "frame_10": {...keypoint data...},
#         ...
#     }
# }
```

---

## Async Workflow with Webhooks

For production systems that can't block on completion.

```python
import synapse
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
client = synapse.Client(api_key="sk_live_xxxx")

WEBHOOK_SECRET = "whsec_xxxxxxxxxxxx"

# =============================================================================
# STEP 1: Create Project and Setup Webhook
# =============================================================================
def create_annotation_job(images: list, job_id: str):
    """Create annotation project and return immediately."""
    
    # Create project
    project = client.projects.create(
        name=f"Annotation Job {job_id}",
        annotation_type="classification",
        labels=["positive", "negative", "neutral"],
        metadata={"job_id": job_id}  # Store reference
    )
    
    # Upload tasks
    tasks = [{"image_url": url, "job_id": job_id} for url in images]
    project.upload_tasks(tasks)
    
    # Setup webhook for this project
    client.webhooks.create(
        url="https://api.yourapp.com/webhooks/synapse",
        events=["project.completed", "task.completed"],
        project_id=project.id,
        secret=WEBHOOK_SECRET
    )
    
    # Pay and start
    project.pay_deposit(payment_method="credits")
    
    # Return immediately - webhook will notify on completion
    return {
        "project_id": project.id,
        "job_id": job_id,
        "status": "processing",
        "task_count": len(images)
    }

# =============================================================================
# STEP 2: Webhook Handler
# =============================================================================
@app.route("/webhooks/synapse", methods=["POST"])
def handle_webhook():
    # Verify signature
    payload = request.get_data()
    signature = request.headers.get("X-Synapse-Signature")
    
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Invalid signature"}), 401
    
    event = request.json
    
    if event["type"] == "project.completed":
        handle_project_completed(event["data"])
    elif event["type"] == "task.completed":
        handle_task_completed(event["data"])
    
    return jsonify({"received": True})

def handle_project_completed(data):
    """Called when entire project is done."""
    project_id = data["project_id"]
    job_id = data.get("metadata", {}).get("job_id")
    
    # Get project and export
    project = client.projects.get(project_id)
    annotations = project.export(format="json")
    
    # Export to S3
    project.export_to_s3(
        bucket="ml-training-data",
        key=f"annotations/{job_id}/results.json",
        format="json"
    )
    
    # Notify your system
    notify_job_complete(job_id, annotations)

def handle_task_completed(data):
    """Called for each completed task (real-time updates)."""
    # Update progress in your database
    update_progress(
        project_id=data["project_id"],
        completed=data["completed_count"],
        total=data["total_count"]
    )

# =============================================================================
# STEP 3: API Endpoint to Start Jobs
# =============================================================================
@app.route("/api/annotate", methods=["POST"])
def start_annotation():
    data = request.json
    images = data["images"]
    job_id = data["job_id"]
    
    result = create_annotation_job(images, job_id)
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5000)
```

---

## High-Volume Production Pipeline

Handle millions of annotations efficiently.

```python
import synapse
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = synapse.Client(
    api_key="sk_live_xxxx",
    timeout=120,
    max_retries=5
)

# =============================================================================
# STEP 1: Batch Project Creation
# =============================================================================
def create_batch_projects(dataset_name: str, total_images: int, batch_size: int = 10000):
    """Split large datasets into manageable project batches."""
    
    projects = []
    num_batches = (total_images + batch_size - 1) // batch_size
    
    for i in range(num_batches):
        project = client.projects.create(
            name=f"{dataset_name} - Batch {i+1}/{num_batches}",
            annotation_type="bounding_box",
            labels=["object_class_1", "object_class_2"],
            metadata={
                "dataset": dataset_name,
                "batch": i + 1,
                "total_batches": num_batches
            },
            priority="normal" if i > 0 else "high"  # First batch high priority
        )
        projects.append(project)
        logger.info(f"Created project {project.id} for batch {i+1}")
    
    return projects

# =============================================================================
# STEP 2: Parallel Upload
# =============================================================================
def upload_to_project(project, s3_prefix):
    """Upload data to a single project."""
    try:
        result = project.upload_from_s3(
            bucket="massive-dataset",
            prefix=s3_prefix,
            file_types=["jpg"]
        )
        logger.info(f"Uploaded {result.task_count} to {project.id}")
        return result
    except Exception as e:
        logger.error(f"Upload failed for {project.id}: {e}")
        raise

def parallel_upload(projects, s3_prefixes):
    """Upload to multiple projects in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(upload_to_project, proj, prefix)
            for proj, prefix in zip(projects, s3_prefixes)
        ]
        results = [f.result() for f in futures]
    return results

# =============================================================================
# STEP 3: Bulk Payment
# =============================================================================
def pay_all_projects(projects):
    """Pay deposits for all projects using credits."""
    total_cost = 0
    
    for project in projects:
        deposit = project.calculate_deposit()
        total_cost += deposit.amount
    
    logger.info(f"Total deposit required: {total_cost}")
    
    # Check balance
    balance = client.billing.get_balance()
    if balance.available < total_cost:
        raise ValueError(f"Insufficient credits: {balance.available} < {total_cost}")
    
    # Pay all deposits
    for project in projects:
        project.pay_deposit(payment_method="credits")
        logger.info(f"Paid deposit for {project.id}")

# =============================================================================
# STEP 4: Aggregate Monitoring
# =============================================================================
def monitor_all_projects(projects, poll_interval=300):
    """Monitor progress across all projects."""
    import time
    
    while True:
        all_complete = True
        total_tasks = 0
        completed_tasks = 0
        
        for project in projects:
            status = project.get_status()
            total_tasks += status.total_tasks
            completed_tasks += status.completed_tasks
            
            if not status.is_complete:
                all_complete = False
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        logger.info(f"Overall progress: {progress:.1f}% ({completed_tasks}/{total_tasks})")
        
        if all_complete:
            logger.info("All projects complete!")
            break
        
        time.sleep(poll_interval)

# =============================================================================
# STEP 5: Aggregate Export
# =============================================================================
def export_all_projects(projects, output_bucket, format="coco"):
    """Export and merge all project annotations."""
    
    all_annotations = []
    
    for project in projects:
        # Export each project to S3
        batch_num = project.metadata.get("batch", "unknown")
        
        project.export_to_s3(
            bucket=output_bucket,
            key=f"annotations/batch_{batch_num}.json",
            format=format
        )
        
        # Also collect for merging
        annotations = project.export(format="json")
        all_annotations.extend(annotations)
    
    logger.info(f"Exported {len(all_annotations)} total annotations")
    return all_annotations

# =============================================================================
# MAIN PIPELINE
# =============================================================================
def run_pipeline():
    # Configuration
    DATASET_NAME = "autonomous_driving_v2"
    TOTAL_IMAGES = 100_000
    BATCH_SIZE = 10_000
    
    # S3 prefixes for each batch
    s3_prefixes = [
        f"images/batch_{i}/" 
        for i in range(TOTAL_IMAGES // BATCH_SIZE)
    ]
    
    # Execute pipeline
    logger.info("Creating projects...")
    projects = create_batch_projects(DATASET_NAME, TOTAL_IMAGES, BATCH_SIZE)
    
    logger.info("Uploading data...")
    parallel_upload(projects, s3_prefixes)
    
    logger.info("Processing payments...")
    pay_all_projects(projects)
    
    logger.info("Monitoring progress...")
    monitor_all_projects(projects)
    
    logger.info("Exporting annotations...")
    export_all_projects(projects, "ml-training-output")
    
    logger.info("Pipeline complete!")

if __name__ == "__main__":
    run_pipeline()
```

---

## Next Steps

- [SDK Reference](sdk-reference.md) - Complete API documentation
- [Annotation Types](annotation-types.md) - Supported annotation formats
- [Webhooks](webhooks.md) - Real-time notifications
- [Error Handling](sdk-reference.md#error-handling) - Handle errors gracefully
