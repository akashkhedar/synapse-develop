"""
Consensus Service for Multi-Annotator Tasks

Handles:
- Consolidation strategies for different annotation types
- Agreement calculation between annotators
- Quality scoring based on consensus
- Payment release based on consensus quality
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from itertools import combinations

logger = logging.getLogger(__name__)


# ============================================================================
# CONSOLIDATION STRATEGIES
# ============================================================================


class ConsolidationStrategy:
    """Base class for annotation consolidation strategies"""

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """
        Consolidate multiple annotations into a single ground truth.

        Args:
            annotations: List of annotation result dicts

        Returns:
            Tuple of (consolidated_result, confidence_score)
        """
        raise NotImplementedError

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """
        Calculate agreement between two annotations.

        Returns:
            Dict with agreement metrics (overall, label, position, etc.)
        """
        raise NotImplementedError


class ClassificationConsolidation(ConsolidationStrategy):
    """
    Consolidation for classification/choices annotations.
    Uses majority voting.
    """

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """Majority voting for classification"""
        if not annotations:
            return {}, 0.0

        # Extract all classification results
        all_choices = []
        for ann in annotations:
            if isinstance(ann, list):
                for item in ann:
                    if item.get("type") in ["choices", "labels", "taxonomy"]:
                        value = item.get("value", {})
                        choices = value.get("choices", [])
                        all_choices.append(tuple(sorted(choices)))
            elif isinstance(ann, dict):
                if ann.get("type") in ["choices", "labels", "taxonomy"]:
                    value = ann.get("value", {})
                    choices = value.get("choices", [])
                    all_choices.append(tuple(sorted(choices)))

        if not all_choices:
            return annotations[0] if annotations else {}, 0.5

        # Count votes
        from collections import Counter

        vote_counts = Counter(all_choices)
        winner, winner_count = vote_counts.most_common(1)[0]

        # Confidence = percentage of annotators who agreed
        confidence = winner_count / len(all_choices)

        # Build consolidated result
        consolidated = []
        for ann in annotations:
            if isinstance(ann, list):
                for item in ann:
                    if item.get("type") in ["choices", "labels", "taxonomy"]:
                        consolidated_item = item.copy()
                        consolidated_item["value"] = {"choices": list(winner)}
                        consolidated.append(consolidated_item)
                        break
            elif isinstance(ann, dict):
                if ann.get("type") in ["choices", "labels", "taxonomy"]:
                    consolidated = ann.copy()
                    consolidated["value"] = {"choices": list(winner)}
                    break

        return consolidated if consolidated else annotations[0], confidence

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for classification"""

        def extract_choices(ann):
            if isinstance(ann, list):
                for item in ann:
                    if item.get("type") in ["choices", "labels", "taxonomy"]:
                        return set(item.get("value", {}).get("choices", []))
            elif isinstance(ann, dict):
                return set(ann.get("value", {}).get("choices", []))
            return set()

        choices1 = extract_choices(ann1)
        choices2 = extract_choices(ann2)

        if not choices1 and not choices2:
            return {"overall": 100.0, "label": 100.0}

        if not choices1 or not choices2:
            return {"overall": 0.0, "label": 0.0}

        # Jaccard similarity
        intersection = len(choices1 & choices2)
        union = len(choices1 | choices2)
        label_agreement = (intersection / union * 100) if union > 0 else 0

        return {"overall": label_agreement, "label": label_agreement}


class BoundingBoxConsolidation(ConsolidationStrategy):
    """
    Advanced consolidation for bounding box annotations.

    Handles:
    - Single vs multiple objects
    - Multiple labels
    - Missing annotations (annotators disagree on object count)
    - Different box shapes for same object
    - Spatial clustering when IoU is ambiguous
    """

    IOU_THRESHOLD = 0.2  # Minimum IoU to consider boxes as same object
    SPATIAL_DISTANCE_THRESHOLD = 0.25  # 25% of image size for spatial proximity
    MIN_ANNOTATOR_AGREEMENT = 0.5  # At least 50% of annotators must agree on an object

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """
        Consolidate bounding boxes using multi-stage clustering:
        1. Group boxes by label
        2. For each label, cluster boxes by spatial proximity and IoU
        3. Average boxes in each cluster
        4. Filter out objects with low annotator agreement
        """
        if not annotations:
            return {}, 0.0

        # Extract all bounding boxes from all annotators
        all_boxes_per_annotator = []
        for ann in annotations:
            boxes = BoundingBoxConsolidation._extract_boxes(ann)
            all_boxes_per_annotator.append(boxes)

        if not all_boxes_per_annotator or not any(all_boxes_per_annotator):
            return annotations[0] if annotations else {}, 0.5

        num_annotators = len(all_boxes_per_annotator)

        # Step 1: Group all boxes by label across all annotators
        boxes_by_label = {}
        for annotator_idx, boxes in enumerate(all_boxes_per_annotator):
            for box in boxes:
                label = tuple(box.get("value", {}).get("rectanglelabels", []))
                if label not in boxes_by_label:
                    boxes_by_label[label] = []
                boxes_by_label[label].append(
                    {"box": box, "annotator_idx": annotator_idx}
                )

        # Step 2: For each label, cluster boxes that represent the same object
        consolidated_boxes = []
        all_confidence_scores = []

        for label, labeled_boxes in boxes_by_label.items():
            # Cluster these boxes to find which ones represent the same object
            clusters = BoundingBoxConsolidation._cluster_boxes(
                labeled_boxes, num_annotators
            )

            # Step 3: Average boxes in each cluster
            for cluster in clusters:
                if (
                    len(cluster)
                    < num_annotators * BoundingBoxConsolidation.MIN_ANNOTATOR_AGREEMENT
                ):
                    # Not enough annotators agreed on this object - skip it
                    continue

                # Average the boxes in this cluster
                boxes_to_average = [item["box"] for item in cluster]
                avg_box = BoundingBoxConsolidation._average_boxes(boxes_to_average)

                # Calculate confidence based on annotator agreement
                unique_annotators = len(set(item["annotator_idx"] for item in cluster))
                confidence = unique_annotators / num_annotators

                consolidated_boxes.append(avg_box)
                all_confidence_scores.append(confidence)

        # Calculate overall confidence
        avg_confidence = (
            sum(all_confidence_scores) / len(all_confidence_scores)
            if all_confidence_scores
            else 0.5
        )

        return consolidated_boxes, avg_confidence

    @staticmethod
    def _cluster_boxes(
        labeled_boxes: List[Dict], num_annotators: int
    ) -> List[List[Dict]]:
        """
        Cluster boxes that likely represent the same object.

        Uses a combination of:
        - IoU (intersection over union)
        - Spatial distance (center-to-center)
        - One box per annotator per cluster (prevents duplicate counting)

        Returns list of clusters, where each cluster is a list of box dicts with 'box' and 'annotator_idx'
        """
        if not labeled_boxes:
            return []

        clusters = []
        used_boxes = set()

        # Sort boxes by x-coordinate for left-to-right processing
        labeled_boxes = sorted(
            labeled_boxes, key=lambda item: item["box"].get("value", {}).get("x", 0)
        )

        for i, item in enumerate(labeled_boxes):
            if i in used_boxes:
                continue

            # Start a new cluster with this box
            cluster = [item]
            used_boxes.add(i)
            annotators_in_cluster = {item["annotator_idx"]}

            # Find all boxes that match this one
            for j, other_item in enumerate(labeled_boxes):
                if j in used_boxes:
                    continue

                # Don't add multiple boxes from same annotator to same cluster
                if other_item["annotator_idx"] in annotators_in_cluster:
                    continue

                # Check if this box matches the cluster
                if BoundingBoxConsolidation._boxes_match(
                    item["box"], other_item["box"], cluster
                ):
                    cluster.append(other_item)
                    used_boxes.add(j)
                    annotators_in_cluster.add(other_item["annotator_idx"])

            clusters.append(cluster)

        return clusters

    @staticmethod
    def _boxes_match(
        box1: Dict, box2: Dict, existing_cluster: List[Dict] = None
    ) -> bool:
        """
        Determine if two boxes represent the same object.

        Uses both IoU and spatial proximity for robust matching.
        If existing_cluster provided, checks if box2 matches the cluster centroid.
        """
        # Calculate IoU
        iou = BoundingBoxConsolidation._calculate_iou(box1, box2)

        if iou >= BoundingBoxConsolidation.IOU_THRESHOLD:
            return True

        # If IoU is low, check spatial proximity (centers are close)
        distance = BoundingBoxConsolidation._calculate_center_distance(box1, box2)

        if distance < BoundingBoxConsolidation.SPATIAL_DISTANCE_THRESHOLD:
            # Centers are close - likely same object with different bounding styles
            return True

        # If we have an existing cluster, check if box2 matches cluster average
        if existing_cluster and len(existing_cluster) > 1:
            cluster_boxes = [item["box"] for item in existing_cluster]
            cluster_avg = BoundingBoxConsolidation._average_boxes(cluster_boxes)

            # Check IoU with cluster average
            iou_with_avg = BoundingBoxConsolidation._calculate_iou(cluster_avg, box2)
            if (
                iou_with_avg >= BoundingBoxConsolidation.IOU_THRESHOLD * 0.8
            ):  # Slightly lower threshold
                return True

        return False

    @staticmethod
    def _calculate_center_distance(box1: Dict, box2: Dict) -> float:
        """
        Calculate normalized distance between box centers.
        Returns value between 0 and ~1.4 (diagonal of unit square).
        """
        try:
            v1 = box1.get("value", {})
            v2 = box2.get("value", {})

            # Calculate centers
            center1_x = v1.get("x", 0) + v1.get("width", 0) / 2
            center1_y = v1.get("y", 0) + v1.get("height", 0) / 2

            center2_x = v2.get("x", 0) + v2.get("width", 0) / 2
            center2_y = v2.get("y", 0) + v2.get("height", 0) / 2

            # Normalize to 0-100 coordinate space (percentage coordinates)
            dx = (center1_x - center2_x) / 100.0
            dy = (center1_y - center2_y) / 100.0

            return (dx * dx + dy * dy) ** 0.5

        except Exception:
            return float("inf")

    @staticmethod
    def _extract_boxes(annotation) -> List[Dict]:
        """Extract bounding box items from annotation"""
        boxes = []
        if isinstance(annotation, list):
            for item in annotation:
                if item.get("type") == "rectanglelabels":
                    boxes.append(item)
        return boxes

    @staticmethod
    def _calculate_iou(box1: Dict, box2: Dict) -> float:
        """Calculate Intersection over Union for two boxes"""
        try:
            v1 = box1.get("value", {})
            v2 = box2.get("value", {})

            x1_1, y1_1 = v1.get("x", 0), v1.get("y", 0)
            w1, h1 = v1.get("width", 0), v1.get("height", 0)
            x2_1, y2_1 = x1_1 + w1, y1_1 + h1

            x1_2, y1_2 = v2.get("x", 0), v2.get("y", 0)
            w2, h2 = v2.get("width", 0), v2.get("height", 0)
            x2_2, y2_2 = x1_2 + w2, y1_2 + h2

            # Intersection
            xi1 = max(x1_1, x1_2)
            yi1 = max(y1_1, y1_2)
            xi2 = min(x2_1, x2_2)
            yi2 = min(y2_1, y2_2)

            inter_width = max(0, xi2 - xi1)
            inter_height = max(0, yi2 - yi1)
            inter_area = inter_width * inter_height

            # Union
            area1 = w1 * h1
            area2 = w2 * h2
            union_area = area1 + area2 - inter_area

            return inter_area / union_area if union_area > 0 else 0.0

        except Exception as e:
            logger.warning(f"Error calculating IoU: {e}")
            return 0.0

    @staticmethod
    def _average_boxes(boxes: List[Dict]) -> Dict:
        """Average multiple boxes into one"""
        if not boxes:
            return {}

        # Average coordinates
        avg_x = sum(b.get("value", {}).get("x", 0) for b in boxes) / len(boxes)
        avg_y = sum(b.get("value", {}).get("y", 0) for b in boxes) / len(boxes)
        avg_w = sum(b.get("value", {}).get("width", 0) for b in boxes) / len(boxes)
        avg_h = sum(b.get("value", {}).get("height", 0) for b in boxes) / len(boxes)

        result = boxes[0].copy()
        result["value"] = {
            **result.get("value", {}),
            "x": avg_x,
            "y": avg_y,
            "width": avg_w,
            "height": avg_h,
        }
        return result

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for bounding boxes"""
        boxes1 = BoundingBoxConsolidation._extract_boxes(ann1)
        boxes2 = BoundingBoxConsolidation._extract_boxes(ann2)

        if not boxes1 and not boxes2:
            return {"overall": 100.0, "iou": 1.0, "label": 100.0}

        if not boxes1 or not boxes2:
            return {"overall": 0.0, "iou": 0.0, "label": 0.0}

        # Calculate average IoU for matching boxes
        total_iou = 0
        matched_count = 0
        label_matches = 0

        for box1 in boxes1:
            best_iou = 0
            label_match = False

            for box2 in boxes2:
                iou = BoundingBoxConsolidation._calculate_iou(box1, box2)
                if iou > best_iou:
                    best_iou = iou
                    label_match = box1.get("value", {}).get(
                        "rectanglelabels"
                    ) == box2.get("value", {}).get("rectanglelabels")

            total_iou += best_iou
            matched_count += 1
            if label_match:
                label_matches += 1

        avg_iou = total_iou / matched_count if matched_count > 0 else 0
        label_agreement = (
            (label_matches / matched_count * 100) if matched_count > 0 else 0
        )

        # Overall is weighted combination of IoU and label agreement
        overall = avg_iou * 100 * 0.6 + label_agreement * 0.4

        return {
            "overall": overall,
            "iou": avg_iou,
            "label": label_agreement,
            "position": avg_iou * 100,
        }


class PolygonConsolidation(ConsolidationStrategy):
    """
    Consolidation for polygon annotations.
    Uses polygon overlap and weighted point averaging.
    """

    OVERLAP_THRESHOLD = 0.4

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """Consolidate polygons using overlap-based clustering"""
        if not annotations:
            return {}, 0.0

        # For now, use voting for labels and average for positions
        all_polygons = []
        for ann in annotations:
            polygons = PolygonConsolidation._extract_polygons(ann)
            all_polygons.append(polygons)

        if not all_polygons or not all_polygons[0]:
            return annotations[0] if annotations else {}, 0.5

        # Use majority voting for which polygons exist
        # Then average their positions
        consolidated = all_polygons[0]  # Start with first annotator
        confidence = 1.0 / len(annotations)

        return consolidated, confidence

    @staticmethod
    def _extract_polygons(annotation) -> List[Dict]:
        """Extract polygon items from annotation"""
        polygons = []
        if isinstance(annotation, list):
            for item in annotation:
                if item.get("type") == "polygonlabels":
                    polygons.append(item)
        return polygons

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for polygons"""
        polys1 = PolygonConsolidation._extract_polygons(ann1)
        polys2 = PolygonConsolidation._extract_polygons(ann2)

        if not polys1 and not polys2:
            return {"overall": 100.0, "label": 100.0}

        if not polys1 or not polys2:
            return {"overall": 0.0, "label": 0.0}

        # Simple label-based agreement for now
        labels1 = set()
        labels2 = set()

        for p in polys1:
            labels1.update(p.get("value", {}).get("polygonlabels", []))
        for p in polys2:
            labels2.update(p.get("value", {}).get("polygonlabels", []))

        if not labels1 and not labels2:
            return {"overall": 100.0, "label": 100.0}

        intersection = len(labels1 & labels2)
        union = len(labels1 | labels2)
        label_agreement = (intersection / union * 100) if union > 0 else 0

        return {"overall": label_agreement, "label": label_agreement}


class NERConsolidation(ConsolidationStrategy):
    """
    Consolidation for Named Entity Recognition (NER) annotations.
    Uses span overlap and label voting.
    """

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """Consolidate NER annotations using span overlap"""
        if not annotations:
            return {}, 0.0

        all_entities = []
        for ann in annotations:
            entities = NERConsolidation._extract_entities(ann)
            all_entities.append(entities)

        if not all_entities or not all_entities[0]:
            return annotations[0] if annotations else {}, 0.5

        # Vote on entities
        entity_votes = {}

        for entities in all_entities:
            for entity in entities:
                start = entity.get("value", {}).get("start", 0)
                end = entity.get("value", {}).get("end", 0)
                labels = tuple(entity.get("value", {}).get("labels", []))
                key = (start, end, labels)

                if key not in entity_votes:
                    entity_votes[key] = {"entity": entity, "count": 0}
                entity_votes[key]["count"] += 1

        # Keep entities with majority votes
        threshold = len(all_entities) / 2
        consolidated = []
        confidence_sum = 0

        for key, data in entity_votes.items():
            if data["count"] >= threshold:
                consolidated.append(data["entity"])
                confidence_sum += data["count"] / len(all_entities)

        avg_confidence = confidence_sum / len(consolidated) if consolidated else 0.5

        return consolidated, avg_confidence

    @staticmethod
    def _extract_entities(annotation) -> List[Dict]:
        """Extract NER entities from annotation"""
        entities = []
        if isinstance(annotation, list):
            for item in annotation:
                if item.get("type") == "labels":
                    entities.append(item)
        return entities

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for NER"""
        ents1 = NERConsolidation._extract_entities(ann1)
        ents2 = NERConsolidation._extract_entities(ann2)

        if not ents1 and not ents2:
            return {"overall": 100.0, "label": 100.0, "position": 100.0}

        if not ents1 or not ents2:
            return {"overall": 0.0, "label": 0.0, "position": 0.0}

        # Check span overlaps
        span_matches = 0
        label_matches = 0

        for e1 in ents1:
            s1 = e1.get("value", {}).get("start", 0)
            e1_end = e1.get("value", {}).get("end", 0)
            l1 = set(e1.get("value", {}).get("labels", []))

            for e2 in ents2:
                s2 = e2.get("value", {}).get("start", 0)
                e2_end = e2.get("value", {}).get("end", 0)
                l2 = set(e2.get("value", {}).get("labels", []))

                # Check span overlap
                overlap_start = max(s1, s2)
                overlap_end = min(e1_end, e2_end)

                if overlap_end > overlap_start:
                    span_matches += 1
                    if l1 == l2:
                        label_matches += 1
                    break

        total_ents = max(len(ents1), len(ents2))
        position_agreement = (span_matches / total_ents * 100) if total_ents > 0 else 0
        label_agreement = (label_matches / total_ents * 100) if total_ents > 0 else 0

        overall = position_agreement * 0.4 + label_agreement * 0.6

        return {
            "overall": overall,
            "label": label_agreement,
            "position": position_agreement,
        }


class SegmentationConsolidation(ConsolidationStrategy):
    """
    Consolidation for segmentation (brush) annotations.
    Uses pixel-wise voting.
    """

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """Consolidate segmentation using majority voting on pixels"""
        if not annotations:
            return {}, 0.0

        # For brush/segmentation, we typically use union or intersection
        # For simplicity, use the annotation with most coverage as base
        return annotations[0] if annotations else {}, 0.5

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for segmentation"""

        # Simplified - check if labels match
        def extract_labels(ann):
            labels = set()
            if isinstance(ann, list):
                for item in ann:
                    if item.get("type") == "brushlabels":
                        labels.update(item.get("value", {}).get("brushlabels", []))
            return labels

        labels1 = extract_labels(ann1)
        labels2 = extract_labels(ann2)

        if not labels1 and not labels2:
            return {"overall": 100.0, "label": 100.0}

        if not labels1 or not labels2:
            return {"overall": 0.0, "label": 0.0}

        intersection = len(labels1 & labels2)
        union = len(labels1 | labels2)
        label_agreement = (intersection / union * 100) if union > 0 else 0

        return {"overall": label_agreement, "label": label_agreement}


class KeypointConsolidation(ConsolidationStrategy):
    """
    Consolidation for keypoint annotations.
    Uses distance-based matching and averaging.
    """

    DISTANCE_THRESHOLD = 5.0  # Percentage of image size

    @staticmethod
    def consolidate(annotations: List[Dict]) -> Tuple[Dict, float]:
        """Consolidate keypoints using distance-based clustering"""
        if not annotations:
            return {}, 0.0

        all_keypoints = []
        for ann in annotations:
            kps = KeypointConsolidation._extract_keypoints(ann)
            all_keypoints.append(kps)

        if not all_keypoints or not all_keypoints[0]:
            return annotations[0] if annotations else {}, 0.5

        # Average keypoint positions with same labels
        keypoint_groups = {}

        for kps in all_keypoints:
            for kp in kps:
                labels = tuple(kp.get("value", {}).get("keypointlabels", []))
                if labels not in keypoint_groups:
                    keypoint_groups[labels] = []
                keypoint_groups[labels].append(kp)

        consolidated = []
        for labels, kps in keypoint_groups.items():
            if len(kps) >= len(all_keypoints) / 2:  # Majority have this keypoint
                avg_x = sum(k.get("value", {}).get("x", 0) for k in kps) / len(kps)
                avg_y = sum(k.get("value", {}).get("y", 0) for k in kps) / len(kps)

                result = kps[0].copy()
                result["value"] = {
                    **result.get("value", {}),
                    "x": avg_x,
                    "y": avg_y,
                }
                consolidated.append(result)

        confidence = (
            len(consolidated) / len(keypoint_groups) if keypoint_groups else 0.5
        )

        return consolidated, confidence

    @staticmethod
    def _extract_keypoints(annotation) -> List[Dict]:
        """Extract keypoint items from annotation"""
        keypoints = []
        if isinstance(annotation, list):
            for item in annotation:
                if item.get("type") == "keypointlabels":
                    keypoints.append(item)
        return keypoints

    @staticmethod
    def calculate_agreement(ann1: Dict, ann2: Dict) -> Dict[str, float]:
        """Calculate agreement for keypoints"""
        kps1 = KeypointConsolidation._extract_keypoints(ann1)
        kps2 = KeypointConsolidation._extract_keypoints(ann2)

        if not kps1 and not kps2:
            return {"overall": 100.0, "label": 100.0, "position": 100.0}

        if not kps1 or not kps2:
            return {"overall": 0.0, "label": 0.0, "position": 0.0}

        # Match keypoints by label and calculate position error
        position_scores = []
        label_matches = 0

        for kp1 in kps1:
            labels1 = set(kp1.get("value", {}).get("keypointlabels", []))
            x1, y1 = kp1.get("value", {}).get("x", 0), kp1.get("value", {}).get("y", 0)

            for kp2 in kps2:
                labels2 = set(kp2.get("value", {}).get("keypointlabels", []))

                if labels1 == labels2:
                    label_matches += 1
                    x2, y2 = kp2.get("value", {}).get("x", 0), kp2.get("value", {}).get(
                        "y", 0
                    )

                    # Euclidean distance as percentage
                    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
                    position_score = max(0, 100 - distance * 10)
                    position_scores.append(position_score)
                    break

        total_kps = max(len(kps1), len(kps2))
        label_agreement = (label_matches / total_kps * 100) if total_kps > 0 else 0
        position_agreement = (
            sum(position_scores) / len(position_scores) if position_scores else 0
        )

        overall = label_agreement * 0.4 + position_agreement * 0.6

        return {
            "overall": overall,
            "label": label_agreement,
            "position": position_agreement,
        }


# ============================================================================
# CONSENSUS SERVICE
# ============================================================================


class ConsensusService:
    """
    Main service for handling multi-annotator consensus.
    Orchestrates consolidation, quality scoring, and payment release.
    """

    # Strategy mapping
    CONSOLIDATION_STRATEGIES = {
        "classification": ClassificationConsolidation,
        "choices": ClassificationConsolidation,
        "bounding_box": BoundingBoxConsolidation,
        "rectanglelabels": BoundingBoxConsolidation,
        "polygon": PolygonConsolidation,
        "polygonlabels": PolygonConsolidation,
        "ner": NERConsolidation,
        "labels": NERConsolidation,
        "segmentation": SegmentationConsolidation,
        "brushlabels": SegmentationConsolidation,
        "keypoint": KeypointConsolidation,
        "keypointlabels": KeypointConsolidation,
    }

    # Quality thresholds
    HIGH_AGREEMENT_THRESHOLD = 80  # Above this = high quality
    LOW_AGREEMENT_THRESHOLD = 50  # Below this = needs review

    # Payment multipliers based on quality
    QUALITY_MULTIPLIERS = {
        "excellent": Decimal("1.2"),  # 90%+ agreement
        "good": Decimal("1.0"),  # 70-90% agreement
        "acceptable": Decimal("0.8"),  # 50-70% agreement
        "poor": Decimal("0.5"),  # Below 50% agreement
    }

    @classmethod
    def get_strategy(cls, annotation_type: str) -> ConsolidationStrategy:
        """Get the appropriate consolidation strategy for annotation type"""
        return cls.CONSOLIDATION_STRATEGIES.get(
            annotation_type.lower(), ClassificationConsolidation  # Default
        )

    @classmethod
    def detect_annotation_type(cls, result: List[Dict]) -> str:
        """Detect annotation type from result"""
        if not result:
            return "classification"

        for item in result:
            if isinstance(item, dict):
                item_type = item.get("type", "").lower()
                if "rectangle" in item_type or "rect" in item_type:
                    return "bounding_box"
                elif "polygon" in item_type:
                    return "polygon"
                elif "keypoint" in item_type:
                    return "keypoint"
                elif "brush" in item_type:
                    return "segmentation"
                elif item_type == "labels":
                    return "ner"
                elif item_type in ["choices", "taxonomy"]:
                    return "classification"

        return "classification"

    @classmethod
    @transaction.atomic
    def check_and_process_consensus(cls, task) -> Optional[Dict]:
        """
        Check if task has enough annotations for consensus and process if ready.

        Returns:
            Dict with consensus results or None if not ready
        """
        from .models import TaskConsensus, TaskAssignment

        project = task.project
        required_overlap = getattr(project, "required_overlap", 1)

        # Get or create consensus record
        consensus, created = TaskConsensus.objects.get_or_create(
            task=task, defaults={"required_annotations": required_overlap}
        )

        # Count completed annotations
        completed_assignments = TaskAssignment.objects.filter(
            task=task, status="completed", annotation__isnull=False
        ).select_related("annotation", "annotator")

        consensus.current_annotations = completed_assignments.count()
        consensus.save(update_fields=["current_annotations"])

        # Check if we have enough annotations
        if consensus.current_annotations < required_overlap:
            logger.debug(
                f"Task {task.id}: {consensus.current_annotations}/{required_overlap} annotations. "
                "Waiting for more."
            )
            return None

        # Ready for consensus processing
        if consensus.status == "pending":
            consensus.status = "in_consensus"
            consensus.save(update_fields=["status"])

        # Process consensus
        return cls._process_consensus(consensus, completed_assignments)

    @classmethod
    @transaction.atomic
    def _process_consensus(cls, consensus, assignments) -> Dict:
        """Process consensus for a task with completed annotations"""
        from .models import AnnotatorAgreement, ConsensusQualityScore

        # Get all annotations
        annotations = []
        for assignment in assignments:
            if assignment.annotation and assignment.annotation.result:
                annotations.append(
                    {
                        "assignment": assignment,
                        "result": assignment.annotation.result,
                    }
                )

        if len(annotations) < 2:
            # Single annotation, no consensus needed
            if annotations:
                consensus.consolidated_result = annotations[0]["result"]
                consensus.status = "consensus_reached"
                consensus.average_agreement = Decimal("100")
                consensus.consensus_reached_at = timezone.now()
                consensus.consolidation_method = "single_annotator"
                consensus.save()

                # Give full quality score to single annotator
                cls._create_quality_score(
                    consensus,
                    annotations[0]["assignment"],
                    Decimal("100"),
                    Decimal("100"),
                )
                cls._release_consensus_payments(consensus)

            return {"status": "single_annotation", "consensus": consensus}

        # Detect annotation type
        annotation_type = cls.detect_annotation_type(annotations[0]["result"])
        strategy = cls.get_strategy(annotation_type)

        # Calculate pairwise agreements
        agreement_scores = []
        for ann1, ann2 in combinations(annotations, 2):
            agreement = strategy.calculate_agreement(ann1["result"], ann2["result"])

            # Store agreement record
            AnnotatorAgreement.objects.update_or_create(
                task_consensus=consensus,
                annotator_1=ann1["assignment"].annotator,
                annotator_2=ann2["assignment"].annotator,
                defaults={
                    "assignment_1": ann1["assignment"],
                    "assignment_2": ann2["assignment"],
                    "agreement_score": Decimal(str(agreement["overall"])),
                    "iou_score": (
                        Decimal(str(agreement.get("iou", 0)))
                        if agreement.get("iou")
                        else None
                    ),
                    "label_agreement": Decimal(str(agreement.get("label", 0))),
                    "position_agreement": (
                        Decimal(str(agreement.get("position", 0)))
                        if agreement.get("position")
                        else None
                    ),
                    "annotation_type": annotation_type,
                    "comparison_details": agreement,
                },
            )
            agreement_scores.append(agreement["overall"])

        # Calculate consensus metrics
        avg_agreement = (
            sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
        )
        min_agreement = min(agreement_scores) if agreement_scores else 0
        max_agreement = max(agreement_scores) if agreement_scores else 0

        consensus.average_agreement = Decimal(str(avg_agreement))
        consensus.min_agreement = Decimal(str(min_agreement))
        consensus.max_agreement = Decimal(str(max_agreement))

        # Consolidate annotations
        results = [ann["result"] for ann in annotations]
        consolidated, confidence = strategy.consolidate(results)

        consensus.consolidated_result = consolidated
        consensus.consolidation_method = strategy.__name__

        # Determine status based on agreement
        if avg_agreement >= cls.HIGH_AGREEMENT_THRESHOLD:
            consensus.status = "consensus_reached"
            consensus.consensus_reached_at = timezone.now()
        elif avg_agreement < cls.LOW_AGREEMENT_THRESHOLD:
            consensus.status = "conflict"
        else:
            consensus.status = "consensus_reached"
            consensus.consensus_reached_at = timezone.now()

        consensus.save()

        # Calculate individual quality scores
        for ann in annotations:
            individual_agreement = strategy.calculate_agreement(
                ann["result"], consolidated
            )
            quality_score = Decimal(str(individual_agreement["overall"]))

            # Calculate average peer agreement
            peer_agreements = []
            for other in annotations:
                if other["assignment"].id != ann["assignment"].id:
                    peer_agreement = strategy.calculate_agreement(
                        ann["result"], other["result"]
                    )
                    peer_agreements.append(peer_agreement["overall"])

            avg_peer = (
                Decimal(str(sum(peer_agreements) / len(peer_agreements)))
                if peer_agreements
                else Decimal("0")
            )

            cls._create_quality_score(
                consensus,
                ann["assignment"],
                quality_score,
                avg_peer,
                individual_agreement,
            )

        # Check if expert review is needed
        expert_review_result = cls._check_for_expert_review(consensus)

        # Release consensus payments if agreement is good enough (and no expert review needed)
        if (
            consensus.status in ["consensus_reached", "finalized"]
            and not expert_review_result
        ):
            cls._release_consensus_payments(consensus)

        return {
            "status": consensus.status,
            "average_agreement": float(avg_agreement),
            "consolidated_result": consolidated,
            "confidence": confidence,
            "consensus": consensus,
        }

    @classmethod
    def _create_quality_score(
        cls,
        consensus,
        assignment,
        quality_score: Decimal,
        avg_peer_agreement: Decimal,
        details: Dict = None,
    ):
        """Create or update quality score for an assignment"""
        from .models import ConsensusQualityScore

        # Calculate quality multiplier
        if quality_score >= 90:
            multiplier = cls.QUALITY_MULTIPLIERS["excellent"]
        elif quality_score >= 70:
            multiplier = cls.QUALITY_MULTIPLIERS["good"]
        elif quality_score >= 50:
            multiplier = cls.QUALITY_MULTIPLIERS["acceptable"]
        else:
            multiplier = cls.QUALITY_MULTIPLIERS["poor"]

        ConsensusQualityScore.objects.update_or_create(
            task_consensus=consensus,
            task_assignment=assignment,
            defaults={
                "annotator": assignment.annotator,
                "quality_score": quality_score,
                "label_accuracy": (
                    Decimal(str(details.get("label", 0))) if details else None
                ),
                "position_accuracy": (
                    Decimal(str(details.get("position", 0)))
                    if details and details.get("position")
                    else None
                ),
                "completeness_score": (
                    Decimal(str(details.get("completeness", 100)))
                    if details
                    else Decimal("100")
                ),
                "avg_peer_agreement": avg_peer_agreement,
                "quality_multiplier": multiplier,
            },
        )

        # Update assignment quality
        assignment.quality_score = quality_score
        assignment.quality_multiplier = multiplier
        assignment.consensus_agreement = avg_peer_agreement
        assignment.save(
            update_fields=["quality_score", "quality_multiplier", "consensus_agreement"]
        )

    @classmethod
    @transaction.atomic
    def _release_consensus_payments(cls, consensus):
        """Release consensus payments (40%) for all assignments with quality multipliers"""
        from .models import ConsensusQualityScore, EarningsTransaction

        quality_scores = ConsensusQualityScore.objects.filter(
            task_consensus=consensus, consensus_payment_released=False
        ).select_related("task_assignment", "annotator")

        for qs in quality_scores:
            assignment = qs.task_assignment
            annotator = qs.annotator

            if not assignment.immediate_released:
                # Immediate payment wasn't released yet, skip
                continue

            if assignment.consensus_released:
                # Already released
                continue

            # Calculate final consensus payment with quality multiplier
            final_payment = (
                assignment.consensus_payment
                * qs.quality_multiplier
                * assignment.trust_multiplier
            )

            # Update assignment
            assignment.consensus_released = True
            assignment.amount_paid += final_payment
            assignment.save(update_fields=["consensus_released", "amount_paid"])

            # Update annotator earnings
            # Move immediate payment from pending to available
            immediate_amount = (
                assignment.immediate_payment
                * assignment.quality_multiplier
                * assignment.trust_multiplier
            )
            annotator.pending_approval -= immediate_amount
            annotator.available_balance += immediate_amount + final_payment
            annotator.total_earned += final_payment
            annotator.save(
                update_fields=["pending_approval", "available_balance", "total_earned"]
            )

            # Record transaction
            EarningsTransaction.objects.create(
                annotator=annotator,
                transaction_type="earning",
                earning_stage="consensus",
                amount=final_payment,
                balance_after=annotator.available_balance,
                task_assignment=assignment,
                description=(
                    f"Consensus payment (40%) for task {assignment.task_id} "
                    f"(Quality: {qs.quality_score}%, Multiplier: {qs.quality_multiplier}x)"
                ),
                metadata={
                    "task_id": assignment.task_id,
                    "quality_score": float(qs.quality_score),
                    "quality_multiplier": float(qs.quality_multiplier),
                    "trust_multiplier": float(assignment.trust_multiplier),
                    "consensus_agreement": float(consensus.average_agreement or 0),
                },
            )

            # Mark quality score as paid
            qs.consensus_payment_released = True
            qs.consensus_payment_amount = final_payment
            qs.save(
                update_fields=["consensus_payment_released", "consensus_payment_amount"]
            )

            logger.info(
                f"Released consensus payment for {annotator.user.email}: "
                f"₹{final_payment} (Quality: {qs.quality_score}%)"
            )

        # Update annotator trust levels
        for qs in quality_scores:
            try:
                trust_level = qs.annotator.trust_level
                trust_level.update_metrics(qs.task_assignment)
            except Exception as e:
                logger.warning(f"Error updating trust level: {e}")

    @classmethod
    def _check_for_expert_review(cls, consensus) -> Optional[Dict]:
        """
        Check if task needs expert review and assign if needed.

        Returns:
            Dict with expert assignment result or None if no review needed
        """
        try:
            from .expert_service import ExpertService

            # Check project settings for expert review
            project = consensus.task.project

            # Check if project has expert review enabled
            expert_review_enabled = getattr(project, "expert_review_enabled", True)
            if not expert_review_enabled:
                return None

            # Use expert service to check and assign
            result = ExpertService.check_and_assign_expert_review(consensus)

            if result and result.get("assigned"):
                logger.info(
                    f"Task {consensus.task_id} assigned to expert review: "
                    f"{result.get('expert_email')} (reason: {result.get('reason')})"
                )
                return result

            return result

        except Exception as e:
            logger.warning(
                f"Error checking expert review for task {consensus.task_id}: {e}"
            )
            return None

    @classmethod
    def get_task_consensus_status(cls, task) -> Dict:
        """Get consensus status for a task"""
        from .models import TaskConsensus

        try:
            consensus = TaskConsensus.objects.get(task=task)
            return {
                "status": consensus.status,
                "current_annotations": consensus.current_annotations,
                "required_annotations": consensus.required_annotations,
                "average_agreement": float(consensus.average_agreement or 0),
                "is_complete": consensus.is_complete,
                "needs_review": consensus.needs_review,
                "consolidated_result": consensus.consolidated_result,
            }
        except TaskConsensus.DoesNotExist:
            project = task.project
            return {
                "status": "pending",
                "current_annotations": 0,
                "required_annotations": getattr(project, "required_overlap", 1),
                "average_agreement": None,
                "is_complete": False,
                "needs_review": False,
                "consolidated_result": None,
            }

    @classmethod
    def finalize_consensus(cls, task, reviewed_by=None, review_notes="") -> Dict:
        """Finalize consensus after expert review"""
        from .models import TaskConsensus

        try:
            consensus = TaskConsensus.objects.get(task=task)
        except TaskConsensus.DoesNotExist:
            return {"error": "No consensus record found"}

        consensus.status = "finalized"
        consensus.finalized_at = timezone.now()
        if reviewed_by:
            consensus.reviewed_by = reviewed_by
            consensus.review_notes = review_notes
        consensus.save()

        # Release review payments (final 20%)
        cls._release_review_payments(consensus)

        return {
            "status": "finalized",
            "task_id": task.id,
        }

    @classmethod
    @transaction.atomic
    def _release_review_payments(cls, consensus):
        """Release final review payments (20%) after expert review"""
        from .models import TaskAssignment, EarningsTransaction

        assignments = TaskAssignment.objects.filter(
            task=consensus.task,
            status="completed",
            consensus_released=True,
            review_released=False,
        ).select_related("annotator")

        for assignment in assignments:
            annotator = assignment.annotator

            # Calculate final review payment
            final_payment = (
                assignment.review_payment
                * assignment.quality_multiplier
                * assignment.trust_multiplier
            )

            # Update assignment
            assignment.review_released = True
            assignment.amount_paid += final_payment
            assignment.save(update_fields=["review_released", "amount_paid"])

            # Update annotator earnings
            annotator.available_balance += final_payment
            annotator.total_earned += final_payment
            annotator.save(update_fields=["available_balance", "total_earned"])

            # Record transaction
            EarningsTransaction.objects.create(
                annotator=annotator,
                transaction_type="earning",
                earning_stage="review",
                amount=final_payment,
                balance_after=annotator.available_balance,
                task_assignment=assignment,
                description=f"Review payment (20%) for task {assignment.task_id}",
                metadata={
                    "task_id": assignment.task_id,
                    "quality_multiplier": float(assignment.quality_multiplier),
                    "trust_multiplier": float(assignment.trust_multiplier),
                },
            )

            logger.info(
                f"Released review payment for {annotator.user.email}: ₹{final_payment}"
            )

    @classmethod
    def calculate_agreement(cls, task, annotations):
        """
        Calculate agreement scores for a set of annotations on a task.

        Args:
            task: Task instance
            annotations: QuerySet of Annotation objects

        Returns:
            Dict with agreement metrics:
            - average_agreement: float
            - min_agreement: float
            - max_agreement: float
            - consolidated_result: dict
            - method: str
        """
        from itertools import combinations

        if annotations.count() < 2:
            # Single annotation - return 100% agreement
            first_ann = annotations.first()
            return {
                "average_agreement": 100.0,
                "min_agreement": 100.0,
                "max_agreement": 100.0,
                "consolidated_result": first_ann.result if first_ann else None,
                "method": "single_annotator",
            }

        # Get annotation results
        ann_list = []
        for ann in annotations:
            if ann.result:
                ann_list.append(
                    {
                        "id": ann.id,
                        "result": ann.result,
                        "user": ann.completed_by,
                    }
                )

        if len(ann_list) < 2:
            return {
                "average_agreement": 100.0,
                "min_agreement": 100.0,
                "max_agreement": 100.0,
                "consolidated_result": ann_list[0]["result"] if ann_list else None,
                "method": "single_annotator",
            }

        # Detect annotation type
        annotation_type = cls.detect_annotation_type(ann_list[0]["result"])
        strategy = cls.get_strategy(annotation_type)

        # Calculate pairwise agreements
        agreement_scores = []
        for ann1, ann2 in combinations(ann_list, 2):
            agreement = strategy.calculate_agreement(ann1["result"], ann2["result"])
            agreement_scores.append(agreement["overall"])

        # Calculate metrics
        avg_agreement = (
            sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
        )
        min_agreement = min(agreement_scores) if agreement_scores else 0
        max_agreement = max(agreement_scores) if agreement_scores else 0

        # Consolidate
        results = [ann["result"] for ann in ann_list]
        consolidated, confidence = strategy.consolidate(results)

        return {
            "average_agreement": avg_agreement,
            "min_agreement": min_agreement,
            "max_agreement": max_agreement,
            "consolidated_result": consolidated,
            "method": strategy.__name__,
            "confidence": confidence,
        }





