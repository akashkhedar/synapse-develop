# Supported Annotation Types

Synapse supports a wide range of annotation types for different ML use cases.

## Overview

| Category | Annotation Types | Data Types |
|----------|------------------|------------|
| Classification | Single-label, Multi-label | Image, Text, Audio, Video |
| Object Detection | Bounding Box, Rotated Box, Polygon | Image, Video |
| Segmentation | Semantic, Instance, Panoptic | Image |
| Keypoints | Skeleton, Landmarks | Image, Video |
| Text | NER, Classification, Sentiment, QA | Text, Document |
| Audio | Transcription, Speaker ID, Emotion | Audio |
| Video | Temporal, Action, Tracking | Video |

---

## Image Annotations

### Classification

Assign one or more labels to an entire image.

```python
# Single-label classification
project = client.projects.create(
    name="Animal Classification",
    annotation_type="classification",
    data_type="image",
    labels=["dog", "cat", "bird", "fish", "other"]
)

# Multi-label classification
project = client.projects.create(
    name="Image Tagging",
    annotation_type="multi_classification",
    data_type="image",
    labels=["outdoor", "indoor", "people", "animals", "vehicles", "nature"]
)
```

**Output Format:**

```json
{
  "classification": {
    "label": "dog",
    "confidence": 0.95
  }
}

// Multi-label
{
  "classifications": [
    {"label": "outdoor", "confidence": 0.92},
    {"label": "nature", "confidence": 0.88}
  ]
}
```

---

### Bounding Box

Draw rectangular boxes around objects.

```python
project = client.projects.create(
    name="Vehicle Detection",
    annotation_type="bounding_box",
    data_type="image",
    labels=["car", "truck", "motorcycle", "bicycle", "bus"]
)
```

**Output Format:**

```json
{
  "bounding_boxes": [
    {
      "label": "car",
      "x": 120,
      "y": 80,
      "width": 200,
      "height": 150,
      "rotation": 0,
      "confidence": 0.94
    },
    {
      "label": "truck",
      "x": 450,
      "y": 100,
      "width": 300,
      "height": 200,
      "rotation": 0,
      "confidence": 0.91
    }
  ]
}
```

**COCO Export:**

```json
{
  "annotations": [
    {
      "id": 1,
      "image_id": 100,
      "category_id": 1,
      "bbox": [120, 80, 200, 150],
      "area": 30000,
      "iscrowd": 0
    }
  ]
}
```

---

### Rotated Bounding Box

Oriented bounding boxes for angled objects.

```python
project = client.projects.create(
    name="Aerial Object Detection",
    annotation_type="rotated_box",
    data_type="image",
    labels=["ship", "plane", "vehicle"]
)
```

**Output Format:**

```json
{
  "rotated_boxes": [
    {
      "label": "ship",
      "cx": 220,
      "cy": 155,
      "width": 200,
      "height": 50,
      "rotation": 45.5,
      "confidence": 0.89
    }
  ]
}
```

---

### Polygon

Precise object outlines using polygon vertices.

```python
project = client.projects.create(
    name="Building Segmentation",
    annotation_type="polygon",
    data_type="image",
    labels=["building", "road", "vegetation", "water"]
)
```

**Output Format:**

```json
{
  "polygons": [
    {
      "label": "building",
      "points": [
        [100, 100], [200, 100], [200, 200], [150, 250], [100, 200]
      ],
      "confidence": 0.92
    }
  ]
}
```

---

### Semantic Segmentation

Pixel-level classification of entire image.

```python
project = client.projects.create(
    name="Street Scene Segmentation",
    annotation_type="segmentation",
    data_type="image",
    labels=[
        "road", "sidewalk", "building", "wall", "fence",
        "pole", "traffic_light", "traffic_sign", "vegetation",
        "terrain", "sky", "person", "rider", "car", "truck",
        "bus", "train", "motorcycle", "bicycle"
    ]
)
```

**Output Format:**

```json
{
  "segmentation": {
    "mask_url": "https://synapse.io/masks/task_123.png",
    "mask_rle": "...",  // Run-length encoding
    "class_map": {
      "0": "background",
      "1": "road",
      "2": "sidewalk"
    }
  }
}
```

---

### Instance Segmentation

Individual object masks with instance IDs.

```python
project = client.projects.create(
    name="Instance Segmentation",
    annotation_type="instance_segmentation",
    data_type="image",
    labels=["person", "car", "dog"]
)
```

**Output Format:**

```json
{
  "instances": [
    {
      "id": 1,
      "label": "person",
      "mask_rle": "...",
      "bbox": [100, 50, 80, 200],
      "area": 12500,
      "confidence": 0.93
    },
    {
      "id": 2,
      "label": "person",
      "mask_rle": "...",
      "bbox": [300, 60, 75, 195],
      "area": 11000,
      "confidence": 0.91
    }
  ]
}
```

---

### Keypoints

Skeleton or landmark detection.

```python
# Human pose estimation
project = client.projects.create(
    name="Human Pose Estimation",
    annotation_type="keypoint",
    data_type="image",
    labels={
        "keypoints": [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ],
        "skeleton": [
            [0, 1], [0, 2], [1, 3], [2, 4],  # Head
            [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],  # Arms
            [5, 11], [6, 12], [11, 12],  # Torso
            [11, 13], [13, 15], [12, 14], [14, 16]  # Legs
        ]
    }
)
```

**Output Format:**

```json
{
  "keypoints": [
    {
      "instance_id": 1,
      "points": {
        "nose": {"x": 150, "y": 50, "visibility": 2},
        "left_eye": {"x": 145, "y": 45, "visibility": 2},
        "right_eye": {"x": 155, "y": 45, "visibility": 2},
        "left_shoulder": {"x": 130, "y": 100, "visibility": 2},
        "right_shoulder": {"x": 170, "y": 100, "visibility": 2}
      },
      "bbox": [100, 30, 100, 250]
    }
  ]
}
```

Visibility values:
- `0`: Not labeled
- `1`: Labeled but occluded
- `2`: Labeled and visible

---

## Text Annotations

### Named Entity Recognition (NER)

Identify and classify named entities in text.

```python
project = client.projects.create(
    name="News Article NER",
    annotation_type="ner",
    data_type="text",
    labels=["PERSON", "ORG", "GPE", "DATE", "MONEY", "EVENT"]
)
```

**Output Format:**

```json
{
  "text": "Apple Inc. announced on January 15, 2025 that Tim Cook...",
  "entities": [
    {
      "start": 0,
      "end": 10,
      "label": "ORG",
      "text": "Apple Inc."
    },
    {
      "start": 24,
      "end": 40,
      "label": "DATE",
      "text": "January 15, 2025"
    },
    {
      "start": 46,
      "end": 54,
      "label": "PERSON",
      "text": "Tim Cook"
    }
  ]
}
```

---

### Text Classification

Classify entire text documents.

```python
project = client.projects.create(
    name="Support Ticket Classification",
    annotation_type="text_classification",
    data_type="text",
    labels=["billing", "technical", "account", "feature_request", "complaint"]
)
```

---

### Sentiment Analysis

Analyze sentiment in text.

```python
project = client.projects.create(
    name="Review Sentiment",
    annotation_type="sentiment",
    data_type="text",
    labels=["positive", "negative", "neutral"]
    # Or use scale: sentiment_scale=5 for 1-5 rating
)
```

**Output Format:**

```json
{
  "sentiment": {
    "label": "positive",
    "score": 0.87
  },
  // Or for scale-based
  "sentiment": {
    "rating": 4,
    "confidence": 0.82
  }
}
```

---

### Question Answering

Extract answers from text.

```python
project = client.projects.create(
    name="Reading Comprehension",
    annotation_type="qa",
    data_type="text"
)

# Upload with questions
tasks = [
    {
        "context": "The Eiffel Tower is located in Paris, France. It was built in 1889...",
        "question": "When was the Eiffel Tower built?"
    }
]
```

**Output Format:**

```json
{
  "answer": {
    "text": "1889",
    "start": 67,
    "end": 71,
    "confidence": 0.95
  }
}
```

---

### Text Span

Highlight specific spans in text.

```python
project = client.projects.create(
    name="Claim Detection",
    annotation_type="text_span",
    data_type="text",
    labels=["claim", "evidence", "conclusion"]
)
```

---

## Audio Annotations

### Transcription

Convert audio to text.

```python
project = client.projects.create(
    name="Podcast Transcription",
    annotation_type="transcription",
    data_type="audio",
    settings={
        "include_timestamps": True,
        "include_speaker_id": True,
        "language": "en"
    }
)
```

**Output Format:**

```json
{
  "transcription": {
    "text": "Welcome to the show. Today we're discussing...",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Welcome to the show.",
        "speaker": "Speaker 1",
        "confidence": 0.95
      },
      {
        "start": 2.5,
        "end": 5.0,
        "text": "Today we're discussing...",
        "speaker": "Speaker 1",
        "confidence": 0.92
      }
    ]
  }
}
```

---

### Audio Classification

Classify audio clips.

```python
project = client.projects.create(
    name="Sound Classification",
    annotation_type="classification",
    data_type="audio",
    labels=["speech", "music", "noise", "silence"]
)
```

---

### Speaker Diarization

Identify different speakers.

```python
project = client.projects.create(
    name="Meeting Diarization",
    annotation_type="speaker_diarization",
    data_type="audio",
    settings={
        "num_speakers": None,  # Auto-detect
        "min_segment_length": 0.5
    }
)
```

---

## Video Annotations

### Video Classification

Classify video clips.

```python
project = client.projects.create(
    name="Action Recognition",
    annotation_type="classification",
    data_type="video",
    labels=["walking", "running", "jumping", "sitting", "standing"]
)
```

---

### Temporal Annotation

Mark time segments in video.

```python
project = client.projects.create(
    name="Video Highlight Detection",
    annotation_type="temporal",
    data_type="video",
    labels=["highlight", "commercial", "intro", "credits"]
)
```

**Output Format:**

```json
{
  "segments": [
    {
      "label": "intro",
      "start": 0.0,
      "end": 15.5
    },
    {
      "label": "highlight",
      "start": 45.0,
      "end": 52.3
    }
  ]
}
```

---

### Video Object Tracking

Track objects across frames.

```python
project = client.projects.create(
    name="Vehicle Tracking",
    annotation_type="tracking",
    data_type="video",
    labels=["car", "pedestrian", "bicycle"],
    settings={
        "frame_rate": 30,
        "interpolation": True
    }
)
```

**Output Format:**

```json
{
  "tracks": [
    {
      "id": 1,
      "label": "car",
      "frames": {
        "0": {"x": 100, "y": 200, "w": 150, "h": 100},
        "5": {"x": 120, "y": 200, "w": 150, "h": 100},
        "10": {"x": 140, "y": 200, "w": 150, "h": 100}
      }
    }
  ]
}
```

---

### Frame-by-Frame Keypoints

Pose estimation across video frames.

```python
project = client.projects.create(
    name="Sports Motion Analysis",
    annotation_type="keypoint",
    data_type="video",
    labels={
        "keypoints": ["head", "shoulders", "elbows", "wrists", "hips", "knees", "ankles"]
    },
    settings={
        "key_frames_only": True,
        "frame_interval": 10
    }
)
```

---

## Multi-Task Annotations

Combine multiple annotation types in one project.

```python
project = client.projects.create(
    name="Comprehensive Image Analysis",
    annotation_type=["classification", "bounding_box", "segmentation"],
    data_type="image",
    labels={
        "classification": ["indoor", "outdoor"],
        "bounding_box": ["person", "vehicle", "animal"],
        "segmentation": ["sky", "ground", "building"]
    },
    instructions="""
    Complete all three annotation tasks:
    1. Classify the scene as indoor or outdoor
    2. Draw bounding boxes around people, vehicles, and animals
    3. Create segmentation masks for sky, ground, and buildings
    """
)
```

**Output Format:**

```json
{
  "classification": {
    "label": "outdoor",
    "confidence": 0.98
  },
  "bounding_boxes": [
    {"label": "person", "x": 100, "y": 150, "width": 80, "height": 200},
    {"label": "vehicle", "x": 400, "y": 200, "width": 200, "height": 150}
  ],
  "segmentation": {
    "mask_url": "https://synapse.io/masks/task_123.png"
  }
}
```

---

## Export Format Reference

### JSON (Default)

```json
{
  "task_id": "task_abc123",
  "data": {"image_url": "..."},
  "result": {...},
  "metadata": {...},
  "created_at": "2025-01-13T10:30:00Z",
  "completed_at": "2025-01-13T14:20:00Z"
}
```

### COCO

Standard COCO format for object detection and segmentation.

```json
{
  "images": [...],
  "annotations": [...],
  "categories": [...]
}
```

### YOLO

YOLO format with normalized coordinates.

```
class_id x_center y_center width height
0 0.5 0.5 0.2 0.3
1 0.25 0.75 0.15 0.2
```

### Pascal VOC

XML format for object detection.

```xml
<annotation>
  <object>
    <name>car</name>
    <bndbox>
      <xmin>100</xmin>
      <ymin>200</ymin>
      <xmax>300</xmax>
      <ymax>350</ymax>
    </bndbox>
  </object>
</annotation>
```

### spaCy (NER)

```python
[
  ("Apple Inc. is a company.", {"entities": [(0, 10, "ORG")]})
]
```

### CoNLL (NER)

```
Apple B-ORG
Inc. I-ORG
is O
a O
company O
```

---

## Quality Settings by Type

| Annotation Type | Recommended Min Annotators | Consensus Threshold | Expert Review |
|-----------------|---------------------------|---------------------|---------------|
| Classification | 3 | 0.66 | Optional |
| Bounding Box | 2-3 | IoU 0.5+ | Recommended |
| Segmentation | 2 | IoU 0.7+ | Recommended |
| Keypoints | 2-3 | Distance threshold | Recommended |
| NER | 2-3 | Token overlap 0.8+ | Recommended |
| Transcription | 1-2 | WER threshold | Optional |

---

## Pricing by Type

| Annotation Type | Complexity | Relative Cost |
|-----------------|------------|---------------|
| Classification | Low | $ |
| Sentiment | Low | $ |
| Bounding Box | Medium | $$ |
| Polygon | Medium-High | $$$ |
| Segmentation | High | $$$$ |
| Keypoints | High | $$$ |
| NER | Medium | $$ |
| Transcription | Medium | $$ (per minute) |
| Video Tracking | Very High | $$$$$ |

Actual pricing depends on:
- Number of labels
- Complexity of instructions
- Quality settings (annotators, consensus)
- Priority level
- Volume discounts

Contact sales for enterprise pricing.
