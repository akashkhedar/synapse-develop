"""
Honeypot Evaluator Service v2.0

Evaluates annotator submissions against golden standard (ground truth).
Supports multiple annotation types with type-specific comparison strategies.

The evaluator:
1. Detects annotation type from ground truth structure
2. Uses appropriate comparator for that type
3. Calculates accuracy score (0-100%)
4. Determines pass/fail based on tolerance
"""

import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HoneypotEvaluator:
    """
    Evaluates annotator submissions against golden standard.
    
    Supports multiple annotation types with type-specific comparison.
    """
    
    @classmethod
    def evaluate(
        cls,
        honeypot_assignment,
        annotator_result: List[Dict]
    ) -> Dict[str, Any]:
        """
        Evaluate annotator's result against golden standard.
        
        Args:
            honeypot_assignment: HoneypotAssignment object
            annotator_result: The annotator's annotation result
            
        Returns:
            {
                'passed': bool,
                'accuracy_score': float (0-100),
                'details': {...}
            }
        """
        golden = honeypot_assignment.golden_standard
        ground_truth = golden.ground_truth
        tolerance = float(golden.tolerance)
        
        # Handle empty results
        if not annotator_result:
            if not ground_truth:
                return {
                    'passed': True,
                    'accuracy_score': 100.0,
                    'details': {
                        'annotation_type': 'empty',
                        'message': 'Both empty - correct'
                    }
                }
            return {
                'passed': False,
                'accuracy_score': 0.0,
                'details': {
                    'annotation_type': 'empty',
                    'message': 'Annotator submitted empty result'
                }
            }
        
        # Detect annotation type from ground truth structure
        annotation_type = cls._detect_annotation_type(ground_truth)
        
        logger.debug(
            f"Evaluating honeypot: type={annotation_type}, "
            f"tolerance={tolerance}"
        )
        
        # Get appropriate comparator for this type
        comparator = cls._get_comparator(annotation_type)
        
        # Calculate accuracy
        comparison_result = comparator.compare(annotator_result, ground_truth)
        overall_score = comparison_result.get('overall_score', 0)
        
        # Determine pass/fail based on tolerance
        # tolerance is 0-1, score is 0-100
        passed = overall_score >= (tolerance * 100)
        
        logger.info(
            f"Honeypot evaluation: score={overall_score:.1f}%, "
            f"tolerance={tolerance*100:.1f}%, passed={passed}"
        )
        
        return {
            'passed': passed,
            'accuracy_score': overall_score,
            'details': {
                'annotation_type': annotation_type,
                'tolerance_required': tolerance * 100,
                'score_achieved': overall_score,
                **comparison_result
            }
        }
    
    @classmethod
    def _detect_annotation_type(cls, result: List[Dict]) -> str:
        """Detect annotation type from result structure."""
        if not result:
            return 'unknown'
        
        # Handle list of annotations
        first_item = result[0] if isinstance(result, list) else result
        
        if not isinstance(first_item, dict):
            return 'unknown'
        
        # Check for 'type' field which indicates annotation type
        if 'type' in first_item:
            type_value = first_item['type'].lower()
            
            type_mapping = {
                'labels': 'classification',
                'choices': 'classification',
                'rectanglelabels': 'bounding_box',
                'rectangle': 'bounding_box',
                'polygonlabels': 'polygon',
                'polygon': 'polygon',
                'brushlabels': 'segmentation',
                'brush': 'segmentation',
                'keypointlabels': 'keypoint',
                'keypoint': 'keypoint',
                'textarea': 'text',
                'text': 'text',
                'rating': 'rating',
                'taxonomy': 'taxonomy',
            }
            return type_mapping.get(type_value, 'generic')
        
        # Check for common annotation structures
        if 'value' in first_item:
            value = first_item.get('value', {})
            if 'choices' in value:
                return 'classification'
            if 'labels' in value:
                return 'classification'
            if 'x' in value and 'y' in value and 'width' in value:
                return 'bounding_box'
            if 'points' in value:
                return 'polygon'
            if 'text' in value:
                return 'text'
        
        return 'generic'
    
    @classmethod
    def _get_comparator(cls, annotation_type: str):
        """Get the appropriate comparator for annotation type."""
        comparators = {
            'classification': ClassificationComparator(),
            'bounding_box': BoundingBoxComparator(),
            'polygon': PolygonComparator(),
            'segmentation': SegmentationComparator(),
            'text': TextComparator(),
            'rating': RatingComparator(),
            'keypoint': KeypointComparator(),
            'generic': GenericComparator(),
            'unknown': GenericComparator(),
        }
        return comparators.get(annotation_type, GenericComparator())


class BaseComparator:
    """Base class for annotation comparators."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        raise NotImplementedError


class ClassificationComparator(BaseComparator):
    """Compare classification/labeling annotations."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        # Extract labels from both results
        annotator_labels = set(self._extract_labels(annotator_result))
        ground_truth_labels = set(self._extract_labels(ground_truth))
        
        if not ground_truth_labels:
            # If no ground truth labels, any answer is wrong
            return {
                'overall_score': 0 if annotator_labels else 100,
                'match': not annotator_labels,
                'message': 'No ground truth labels defined'
            }
        
        # Calculate Jaccard similarity for multi-label classification
        intersection = annotator_labels & ground_truth_labels
        union = annotator_labels | ground_truth_labels
        
        if not union:
            score = 100.0
        else:
            score = (len(intersection) / len(union)) * 100
        
        return {
            'overall_score': score,
            'annotator_labels': list(annotator_labels),
            'expected_labels': list(ground_truth_labels),
            'matches': list(intersection),
            'missing': list(ground_truth_labels - annotator_labels),
            'extra': list(annotator_labels - ground_truth_labels),
            'match': annotator_labels == ground_truth_labels,
        }
    
    def _extract_labels(self, result: List[Dict]) -> List[str]:
        """Extract all labels from annotation result."""
        labels = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            value = item.get('value', {})
            if isinstance(value, dict):
                # Handle choices (single/multi select)
                if 'choices' in value:
                    labels.extend(value['choices'])
                # Handle labels (classification)
                elif 'labels' in value:
                    labels.extend(value['labels'])
        
        return labels


class BoundingBoxComparator(BaseComparator):
    """Compare bounding box annotations using IoU (Intersection over Union)."""
    
    IOU_THRESHOLD = 0.5  # Minimum IoU to consider a match
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        annotator_boxes = self._extract_boxes(annotator_result)
        ground_truth_boxes = self._extract_boxes(ground_truth)
        
        if not ground_truth_boxes:
            return {
                'overall_score': 100 if not annotator_boxes else 0,
                'boxes_expected': 0,
                'boxes_found': len(annotator_boxes),
            }
        
        if not annotator_boxes:
            return {
                'overall_score': 0,
                'boxes_expected': len(ground_truth_boxes),
                'boxes_found': 0,
                'message': 'No boxes annotated'
            }
        
        # Match boxes and calculate IoU
        total_iou = 0
        matched_count = 0
        matched_gt = set()
        box_results = []
        
        for gt_idx, gt_box in enumerate(ground_truth_boxes):
            best_iou = 0
            best_ann_idx = -1
            
            for ann_idx, ann_box in enumerate(annotator_boxes):
                # Labels must match for IoU consideration
                if ann_box.get('label') == gt_box.get('label'):
                    iou = self._calculate_iou(ann_box, gt_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_ann_idx = ann_idx
            
            total_iou += best_iou
            if best_iou >= self.IOU_THRESHOLD:
                matched_count += 1
                matched_gt.add(gt_idx)
            
            box_results.append({
                'ground_truth_idx': gt_idx,
                'label': gt_box.get('label'),
                'best_iou': round(best_iou, 3),
                'matched': best_iou >= self.IOU_THRESHOLD,
            })
        
        # Calculate overall score as average IoU
        overall_score = (total_iou / len(ground_truth_boxes)) * 100
        
        return {
            'overall_score': overall_score,
            'boxes_expected': len(ground_truth_boxes),
            'boxes_found': len(annotator_boxes),
            'boxes_matched': matched_count,
            'average_iou': total_iou / len(ground_truth_boxes),
            'iou_threshold': self.IOU_THRESHOLD,
            'box_details': box_results,
        }
    
    def _extract_boxes(self, result: List[Dict]) -> List[Dict]:
        """Extract bounding boxes from annotation result."""
        boxes = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get('type', '').lower()
            if item_type not in ['rectanglelabels', 'rectangle']:
                continue
            
            value = item.get('value', {})
            if not isinstance(value, dict):
                continue
            
            # Extract label
            label = ''
            if 'rectanglelabels' in value:
                labels = value['rectanglelabels']
                label = labels[0] if labels else ''
            elif 'labels' in value:
                labels = value['labels']
                label = labels[0] if labels else ''
            
            boxes.append({
                'x': value.get('x', 0),
                'y': value.get('y', 0),
                'width': value.get('width', 0),
                'height': value.get('height', 0),
                'label': label,
            })
        
        return boxes
    
    def _calculate_iou(self, box1: Dict, box2: Dict) -> float:
        """Calculate Intersection over Union for two boxes."""
        # Box coordinates (x, y are percentages 0-100)
        x1_1, y1_1 = box1['x'], box1['y']
        x2_1, y2_1 = x1_1 + box1['width'], y1_1 + box1['height']
        
        x1_2, y1_2 = box2['x'], box2['y']
        x2_2, y2_2 = x1_2 + box2['width'], y1_2 + box2['height']
        
        # Intersection coordinates
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        # Intersection area
        intersection = max(0, x2_i - x1_i) * max(0, y2_i - y1_i)
        
        # Union area
        area1 = box1['width'] * box1['height']
        area2 = box2['width'] * box2['height']
        union = area1 + area2 - intersection
        
        if union <= 0:
            return 0.0
        
        return intersection / union


class PolygonComparator(BaseComparator):
    """Compare polygon annotations using simplified area overlap."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        # Simplified comparison - check if same number of polygons with matching labels
        ann_polygons = self._extract_polygons(annotator_result)
        gt_polygons = self._extract_polygons(ground_truth)
        
        if not gt_polygons:
            return {
                'overall_score': 100 if not ann_polygons else 0,
                'polygons_expected': 0,
            }
        
        # Compare labels
        ann_labels = set(p.get('label', '') for p in ann_polygons)
        gt_labels = set(p.get('label', '') for p in gt_polygons)
        
        if ann_labels == gt_labels:
            # Same labels found - give partial credit based on count match
            count_ratio = min(len(ann_polygons), len(gt_polygons)) / max(len(ann_polygons), len(gt_polygons))
            score = count_ratio * 100
        else:
            # Label mismatch
            intersection = ann_labels & gt_labels
            union = ann_labels | gt_labels
            score = (len(intersection) / len(union)) * 100 if union else 0
        
        return {
            'overall_score': score,
            'polygons_expected': len(gt_polygons),
            'polygons_found': len(ann_polygons),
            'labels_expected': list(gt_labels),
            'labels_found': list(ann_labels),
        }
    
    def _extract_polygons(self, result: List[Dict]) -> List[Dict]:
        """Extract polygons from annotation result."""
        polygons = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get('type', '').lower()
            if item_type not in ['polygonlabels', 'polygon']:
                continue
            
            value = item.get('value', {})
            label = ''
            if 'polygonlabels' in value:
                labels = value['polygonlabels']
                label = labels[0] if labels else ''
            
            polygons.append({
                'points': value.get('points', []),
                'label': label,
            })
        
        return polygons


class SegmentationComparator(BaseComparator):
    """Compare segmentation (brush) annotations."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        # For segmentation, compare labels as classification
        ann_labels = self._extract_labels(annotator_result)
        gt_labels = self._extract_labels(ground_truth)
        
        if not gt_labels:
            return {'overall_score': 100 if not ann_labels else 0}
        
        # Jaccard similarity of labels
        intersection = set(ann_labels) & set(gt_labels)
        union = set(ann_labels) | set(gt_labels)
        
        score = (len(intersection) / len(union)) * 100 if union else 0
        
        return {
            'overall_score': score,
            'labels_expected': list(set(gt_labels)),
            'labels_found': list(set(ann_labels)),
        }
    
    def _extract_labels(self, result: List[Dict]) -> List[str]:
        labels = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get('value', {})
            if 'brushlabels' in value:
                labels.extend(value['brushlabels'])
        
        return labels


class TextComparator(BaseComparator):
    """Compare text annotations using string similarity."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        ann_text = self._extract_text(annotator_result)
        gt_text = self._extract_text(ground_truth)
        
        if not gt_text:
            return {
                'overall_score': 100 if not ann_text else 0,
                'message': 'No ground truth text'
            }
        
        if not ann_text:
            return {
                'overall_score': 0,
                'message': 'No text provided'
            }
        
        # Calculate similarity using normalized Levenshtein distance
        similarity = self._calculate_similarity(ann_text, gt_text)
        score = similarity * 100
        
        return {
            'overall_score': score,
            'expected_text': gt_text[:100] + '...' if len(gt_text) > 100 else gt_text,
            'provided_text': ann_text[:100] + '...' if len(ann_text) > 100 else ann_text,
            'similarity': similarity,
        }
    
    def _extract_text(self, result: List[Dict]) -> str:
        """Extract text from annotation result."""
        texts = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get('value', {})
            if 'text' in value:
                text_val = value['text']
                if isinstance(text_val, list):
                    texts.extend(text_val)
                else:
                    texts.append(str(text_val))
        
        return ' '.join(texts).strip()
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate normalized string similarity (0-1)."""
        if s1 == s2:
            return 1.0
        
        # Normalize strings
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Calculate Levenshtein distance
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Simple edit distance calculation
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        distance = dp[len1][len2]
        max_len = max(len1, len2)
        
        return 1 - (distance / max_len)


class RatingComparator(BaseComparator):
    """Compare rating annotations."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        ann_rating = self._extract_rating(annotator_result)
        gt_rating = self._extract_rating(ground_truth)
        
        if gt_rating is None:
            return {'overall_score': 0, 'message': 'No ground truth rating'}
        
        if ann_rating is None:
            return {'overall_score': 0, 'message': 'No rating provided'}
        
        # Exact match = 100%, difference reduces score
        if ann_rating == gt_rating:
            score = 100.0
        else:
            # Assume 5-point scale, calculate distance penalty
            max_distance = 5  # Typical rating scale
            distance = abs(ann_rating - gt_rating)
            score = max(0, (1 - distance / max_distance)) * 100
        
        return {
            'overall_score': score,
            'expected_rating': gt_rating,
            'provided_rating': ann_rating,
        }
    
    def _extract_rating(self, result: List[Dict]) -> Optional[int]:
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get('value', {})
            if 'rating' in value:
                try:
                    return int(value['rating'])
                except (ValueError, TypeError):
                    pass
        
        return None


class KeypointComparator(BaseComparator):
    """Compare keypoint annotations."""
    
    DISTANCE_THRESHOLD = 5.0  # Percentage distance threshold
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        ann_points = self._extract_keypoints(annotator_result)
        gt_points = self._extract_keypoints(ground_truth)
        
        if not gt_points:
            return {'overall_score': 100 if not ann_points else 0}
        
        if not ann_points:
            return {'overall_score': 0, 'message': 'No keypoints provided'}
        
        # Match keypoints by label and calculate distance
        total_score = 0
        matched = 0
        
        for gt_point in gt_points:
            gt_label = gt_point.get('label', '')
            best_distance = float('inf')
            
            for ann_point in ann_points:
                if ann_point.get('label', '') == gt_label:
                    dist = self._calculate_distance(gt_point, ann_point)
                    best_distance = min(best_distance, dist)
            
            if best_distance < float('inf'):
                # Convert distance to score (closer = higher score)
                point_score = max(0, 100 - (best_distance / self.DISTANCE_THRESHOLD) * 100)
                total_score += min(100, point_score)
                matched += 1
        
        overall_score = total_score / len(gt_points) if gt_points else 0
        
        return {
            'overall_score': overall_score,
            'keypoints_expected': len(gt_points),
            'keypoints_found': len(ann_points),
            'keypoints_matched': matched,
        }
    
    def _extract_keypoints(self, result: List[Dict]) -> List[Dict]:
        keypoints = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get('type', '').lower()
            if 'keypoint' not in item_type:
                continue
            
            value = item.get('value', {})
            label = ''
            if 'keypointlabels' in value:
                labels = value['keypointlabels']
                label = labels[0] if labels else ''
            
            keypoints.append({
                'x': value.get('x', 0),
                'y': value.get('y', 0),
                'label': label,
            })
        
        return keypoints
    
    def _calculate_distance(self, p1: Dict, p2: Dict) -> float:
        """Calculate Euclidean distance between two points."""
        dx = p1.get('x', 0) - p2.get('x', 0)
        dy = p1.get('y', 0) - p2.get('y', 0)
        return (dx ** 2 + dy ** 2) ** 0.5


class GenericComparator(BaseComparator):
    """Fallback comparator for unknown annotation types."""
    
    def compare(self, annotator_result: List[Dict], ground_truth: List[Dict]) -> Dict:
        # Try to do a structural comparison
        if annotator_result == ground_truth:
            return {
                'overall_score': 100,
                'match': True,
                'message': 'Exact match'
            }
        
        # Try to extract and compare any 'value' fields
        ann_values = self._extract_values(annotator_result)
        gt_values = self._extract_values(ground_truth)
        
        if ann_values == gt_values:
            return {
                'overall_score': 100,
                'match': True,
                'message': 'Values match'
            }
        
        # Partial matching based on common elements
        if ann_values and gt_values:
            common = set(str(v) for v in ann_values) & set(str(v) for v in gt_values)
            all_vals = set(str(v) for v in ann_values) | set(str(v) for v in gt_values)
            if all_vals:
                score = (len(common) / len(all_vals)) * 100
                return {
                    'overall_score': score,
                    'match': False,
                    'message': 'Partial match'
                }
        
        return {
            'overall_score': 0,
            'match': False,
            'message': 'No match found'
        }
    
    def _extract_values(self, result: List[Dict]) -> List:
        values = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            if isinstance(item, dict) and 'value' in item:
                values.append(item['value'])
        
        return values
