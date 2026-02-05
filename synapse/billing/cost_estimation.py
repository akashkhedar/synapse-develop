"""
Cost Estimation Service for Project Creation

This module provides cost estimation formulas for clients to understand
project costs before creation and after annotation completion.

COST CALCULATION FORMULA:
========================

1. PROJECT CREATION COST (Security Deposit)
   Total Deposit = Security Fee + Storage Fee + Annotation Fee

   Where:
   - Security Fee: 10% of (Storage + Annotation Fee), minimum ₹500
   - Storage Fee: Estimated Storage (GB) × ₹10/GB
   - Annotation Fee: Task Count × Base Rate × Complexity × Buffer × Overlap

2. ANNOTATION WORK COST (Actual Cost)
   Total Cost = Sum of all annotation costs per task

   Where:
   - Each annotation = Base Rate × Annotation Type Multiplier × Complexity Factor
   - Base Rate depends on data type and annotation type
   - Complexity Multiplier based on label config (number of labels, types, etc.)
   - Buffer Multiplier: 1.5x (for estimation safety margin)
   - Overlap Multiplier: Number of annotators per task (default: 3)

OVERLAP (CONSENSUS):
===================
Each task requires multiple annotations for quality validation:
- Default overlap: 3 annotators per task
- Total annotations = Task Count × Overlap
- Cost scales linearly with overlap

ANNOTATION TYPE RATES:
=====================
- Classification: ₹2 per task
- Bounding Box: ₹5 per task
- Polygon/Segmentation: ₹10 per task
- Keypoint: ₹8 per task
- Text Annotation: ₹3 per task
- Audio Transcription: ₹15 per minute
- Video Annotation: ₹20 per minute

COMPLEXITY MULTIPLIERS:
======================
- Simple (1-5 labels): 1.0x
- Medium (6-15 labels): 1.5x
- Complex (16-30 labels): 2.0x
- Very Complex (31+ labels): 3.0x

Multiple annotation types: Add 0.5x per additional type

EXAMPLE CALCULATION:
===================
Project with:
- 100 tasks
- Bounding box annotation
- 10 labels
- 1GB storage estimate
- 3 annotators per task (default overlap)

Step 1: Annotation Rate = ₹5 (bounding box)
Step 2: Complexity Multiplier = 1.5x (6-15 labels)
Step 3: Buffer Multiplier = 1.5x
Step 4: Overlap = 3
Step 5: Annotation Fee = 100 × ₹5 × 1.5 × 1.5 × 3 = ₹3,375
Step 6: Storage Fee = 1 GB × ₹10/GB = ₹10
Step 7: Security Fee = max(₹500, 10% × (₹10 + ₹3,375)) = ₹339 → ₹500 (min)

Total Deposit = ₹500 + ₹10 + ₹3,375 = ₹3,885

After completion, actual cost may be less if fewer annotations were created,
and unused deposit will be refunded.
"""

from decimal import Decimal
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class CostEstimationService:
    """Service for estimating project costs"""
    
    # Base constants
    BASE_DEPOSIT_FEE = Decimal("500")  # Minimum security fee
    STORAGE_RATE_PER_GB = Decimal("10")
    ANNOTATION_BUFFER_MULTIPLIER = Decimal("1.5")
    SECURITY_FEE_PERCENTAGE = Decimal("0.10")  # 10% of project cost
    
    @classmethod
    def calculate_security_fee(cls, storage_fee: Decimal, annotation_fee: Decimal) -> Decimal:
        """
        Calculate security fee as 10% of project cost (storage + annotation).
        Minimum security fee is ₹500.
        
        Formula: Security Fee = max(500, round(10% of (Storage Fee + Annotation Fee)))
        
        Args:
            storage_fee: Calculated storage fee
            annotation_fee: Calculated annotation fee
            
        Returns:
            Decimal: Security fee amount (minimum ₹500)
        """
        from decimal import ROUND_HALF_UP
        
        # Calculate 10% of project cost (storage + annotation)
        project_cost = storage_fee + annotation_fee
        security_fee = project_cost * cls.SECURITY_FEE_PERCENTAGE
        
        # Round to nearest whole number
        security_fee = security_fee.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        # Apply minimum of ₹500
        if security_fee < cls.BASE_DEPOSIT_FEE:
            return cls.BASE_DEPOSIT_FEE
        
        return security_fee
    
    # Annotation type base rates (₹ per task)
    ANNOTATION_RATES = {
        "classification": Decimal("2"),
        "choices": Decimal("2"),
        "labels": Decimal("3"),
        "rectanglelabels": Decimal("5"),
        "polygonlabels": Decimal("10"),
        "keypointlabels": Decimal("8"),
        "brushlabels": Decimal("12"),
        "ellipselabels": Decimal("6"),
        "textarea": Decimal("3"),
        "textarealabels": Decimal("4"),
        "hypertextlabels": Decimal("4"),
        "timeserieslabels": Decimal("7"),
        "videorectangle": Decimal("15"),
    }
    
    # Duration-based rates (₹ per minute)
    DURATION_RATES = {
        "audio": Decimal("15"),
        "video": Decimal("20"),
    }
    
    # Complexity multipliers based on label count
    COMPLEXITY_TIERS = [
        (5, Decimal("1.0"), "Simple"),
        (15, Decimal("1.5"), "Medium"),
        (30, Decimal("2.0"), "Complex"),
        (float('inf'), Decimal("3.0"), "Very Complex"),
    ]
    
    # Default overlap for cost estimation (matches project default)
    DEFAULT_OVERLAP = 3
    
    @classmethod
    def estimate_project_cost(
        cls,
        task_count: int,
        label_config: Optional[str] = None,
        estimated_storage_gb: Optional[float] = None,
        avg_duration_mins: Optional[float] = None,
        annotation_types: Optional[List[str]] = None,
        label_count: Optional[int] = None,
        required_overlap: Optional[int] = None,
    ) -> Dict:
        """
        Estimate total project cost including deposit and annotation work
        
        Args:
            task_count: Number of tasks in project
            label_config: Label Studio XML config (for auto-detection)
            estimated_storage_gb: Estimated storage in GB
            avg_duration_mins: Average duration for audio/video (minutes)
            annotation_types: List of annotation types (if not auto-detecting)
            label_count: Number of labels (if not auto-detecting)
            required_overlap: Number of annotators per task (default: 3)
            
        Returns:
            Dict with detailed cost breakdown
        """
        
        # Use default overlap if not specified
        overlap = required_overlap if required_overlap is not None else cls.DEFAULT_OVERLAP
        
        # Analyze label config if provided
        if label_config:
            config_analysis = cls._analyze_label_config(label_config)
            detected_annotation_types = config_analysis["annotation_types"]
            detected_label_count = config_analysis["total_labels"]
            detected_data_types = config_analysis["data_types"]
        else:
            detected_annotation_types = annotation_types or ["rectanglelabels"]
            detected_label_count = label_count or 5
            detected_data_types = ["image"]
        
        # Calculate storage fee first
        storage_fee = Decimal(str(estimated_storage_gb or 0)) * cls.STORAGE_RATE_PER_GB
        
        # Calculate annotation rate
        annotation_rate = cls._calculate_annotation_rate(detected_annotation_types)
        
        # Check for duration-based pricing
        is_duration_based = any(dt in ["audio", "video"] for dt in detected_data_types)
        if is_duration_based:
            data_type = next((dt for dt in detected_data_types if dt in ["audio", "video"]), "image")
            duration_rate = cls.DURATION_RATES.get(data_type, Decimal("15"))
            if avg_duration_mins:
                annotation_rate = duration_rate * Decimal(str(avg_duration_mins))
            else:
                # Default: 3 minutes per task for audio, 5 for video
                default_duration = 3 if data_type == "audio" else 5
                annotation_rate = duration_rate * Decimal(str(default_duration))
        
        # Calculate complexity multiplier
        complexity_multiplier, complexity_level = cls._get_complexity_multiplier(
            detected_label_count,
            len(detected_annotation_types)
        )
        
        # Calculate estimated annotation cost (multiplied by overlap)
        # Each task needs annotations from `overlap` number of annotators
        estimated_annotation_cost = (
            Decimal(str(task_count))
            * annotation_rate
            * complexity_multiplier
            * cls.ANNOTATION_BUFFER_MULTIPLIER
            * Decimal(str(overlap))
        )
        
        # Calculate security fee as 10% of project cost (storage + annotation)
        security_fee = cls.calculate_security_fee(storage_fee, estimated_annotation_cost)
        base_fee = security_fee  # For backward compatibility
        
        # Total deposit (what client pays upfront)
        total_deposit = security_fee + storage_fee + estimated_annotation_cost
        
        # Actual annotation cost (without buffer - expected actual cost)
        actual_annotation_cost = (
            Decimal(str(task_count))
            * annotation_rate
            * complexity_multiplier
            * Decimal(str(overlap))
        )
        
        # Expected refund (buffer amount)
        expected_refund = estimated_annotation_cost - actual_annotation_cost
        
        return {
            "deposit_breakdown": {
                "base_fee": float(base_fee),
                "storage_fee": float(storage_fee),
                "annotation_fee": float(estimated_annotation_cost),
                "total_deposit": float(total_deposit),
            },
            "annotation_breakdown": {
                "task_count": task_count,
                "required_overlap": overlap,
                "total_annotations": task_count * overlap,
                "annotation_rate_per_task": float(annotation_rate),
                "complexity_multiplier": float(complexity_multiplier),
                "complexity_level": complexity_level,
                "buffer_multiplier": float(cls.ANNOTATION_BUFFER_MULTIPLIER),
                "actual_annotation_cost": float(actual_annotation_cost),
                "expected_refund": float(expected_refund),
            },
            "project_details": {
                "annotation_types": detected_annotation_types,
                "data_types": detected_data_types,
                "total_labels": detected_label_count,
                "storage_gb": float(estimated_storage_gb or 0),
                "is_duration_based": is_duration_based,
            },
            "cost_summary": {
                "upfront_deposit": float(total_deposit),
                "expected_actual_cost": float(base_fee + storage_fee + actual_annotation_cost),
                "expected_refund": float(expected_refund),
                "cost_per_task": float(annotation_rate * complexity_multiplier),
                "cost_per_task_with_overlap": float(annotation_rate * complexity_multiplier * Decimal(str(overlap))),
            },
            "formula_explanation": {
                "deposit_formula": "Security Fee + Storage Fee + Annotation Fee",
                "annotation_fee_formula": f"Tasks ({task_count}) × Rate (₹{annotation_rate}) × Complexity ({complexity_multiplier}) × Buffer (1.5) × Overlap ({overlap})",
                "security_fee_formula": "max(₹500, round(10% × (Storage Fee + Annotation Fee)))",
                "buffer_explanation": "1.5x buffer added to deposit for safety - unused amount refunded after completion",
                "overlap_explanation": f"Each task requires {overlap} annotators for consensus validation",
            },
        }
    
    @classmethod
    def _analyze_label_config(cls, label_config: str) -> Dict:
        """Analyze label config to detect annotation types and complexity"""
        
        if not label_config:
            return {
                "annotation_types": ["rectanglelabels"],
                "total_labels": 5,
                "complexity_multiplier": Decimal("1.0"),
                "data_types": ["image"],
                "detected_tags": [],
            }
        
        # Detect annotation control tags
        annotation_tags = [
            "Choices", "Labels", "RectangleLabels", "PolygonLabels",
            "KeyPointLabels", "BrushLabels", "EllipseLabels",
            "TextArea", "TextAreaLabels", "HyperTextLabels",
            "TimeSeriesLabels", "VideoRectangle",
        ]
        
        detected_types = []
        for tag in annotation_tags:
            if f"<{tag}" in label_config or f"<{tag.lower()}" in label_config:
                detected_types.append(tag.lower())
        
        # Count total labels
        label_pattern = r'<Label\s+value="[^"]*"'
        labels = re.findall(label_pattern, label_config, re.IGNORECASE)
        total_labels = len(labels)
        
        # Detect data types
        data_types = []
        if "<Image" in label_config or "<image" in label_config:
            data_types.append("image")
        if "<Audio" in label_config or "<audio" in label_config:
            data_types.append("audio")
        if "<Video" in label_config or "<video" in label_config:
            data_types.append("video")
        if "<Text" in label_config or "<text" in label_config:
            data_types.append("text")
        
        if not data_types:
            data_types = ["image"]
        
        # Get complexity multiplier
        complexity_multiplier, _ = cls._get_complexity_multiplier(
            total_labels, len(detected_types)
        )
        
        return {
            "annotation_types": detected_types or ["rectanglelabels"],
            "total_labels": total_labels,
            "complexity_multiplier": complexity_multiplier,
            "data_types": data_types,
            "detected_tags": detected_types,
        }
    
    @classmethod
    def _calculate_annotation_rate(cls, annotation_types: List[str]) -> Decimal:
        """Calculate base annotation rate from detected types"""
        
        if not annotation_types:
            return cls.ANNOTATION_RATES.get("rectanglelabels", Decimal("5"))
        
        # Get highest rate from detected types
        max_rate = Decimal("0")
        for ann_type in annotation_types:
            rate = cls.ANNOTATION_RATES.get(ann_type.lower(), Decimal("5"))
            if rate > max_rate:
                max_rate = rate
        
        # Add 20% for each additional annotation type
        if len(annotation_types) > 1:
            additional_multiplier = Decimal("1.0") + (Decimal("0.2") * (len(annotation_types) - 1))
            max_rate = max_rate * additional_multiplier
        
        return max_rate
    
    @classmethod
    def _get_complexity_multiplier(cls, label_count: int, annotation_type_count: int) -> tuple:
        """Get complexity multiplier based on label count and annotation types"""
        
        # Base multiplier from label count
        base_multiplier = Decimal("1.0")
        level = "Simple"
        
        for threshold, multiplier, level_name in cls.COMPLEXITY_TIERS:
            if label_count <= threshold:
                base_multiplier = multiplier
                level = level_name
                break
        
        # Add multiplier for multiple annotation types
        if annotation_type_count > 1:
            type_multiplier = Decimal("0.5") * (annotation_type_count - 1)
            base_multiplier += type_multiplier
            if annotation_type_count > 2:
                level = f"{level} + Multi-type"
        
        return base_multiplier, level
    
    @classmethod
    def get_formula_documentation(cls) -> str:
        """Return human-readable formula documentation"""
        return __doc__
    
    @classmethod
    def get_task_annotation_slot_counts(cls, task_ids: List[int], overlap: int = None) -> Dict:
        """
        Get annotation count per task for refund calculations.
        
        Args:
            task_ids: List of task IDs to check
            overlap: Maximum overlap per task (default: DEFAULT_OVERLAP)
            
        Returns:
            Dict with task_id -> annotation_count (capped at overlap)
        """
        from tasks.models import Annotation
        from django.db.models import Count
        
        if overlap is None:
            overlap = cls.DEFAULT_OVERLAP
        
        # Get raw counts
        counts = dict(
            Annotation.objects.filter(task_id__in=task_ids)
            .values('task_id')
            .annotate(count=Count('id'))
            .values_list('task_id', 'count')
        )
        
        # Cap at overlap limit and fill missing with 0
        result = {}
        for task_id in task_ids:
            raw_count = counts.get(task_id, 0)
            result[task_id] = min(raw_count, overlap)
        
        return result
    
    @classmethod
    def calculate_slot_based_refund(
        cls,
        task_ids: List[int],
        cost_per_slot: Decimal,
        overlap: int = None,
    ) -> Dict:
        """
        Calculate refund based on unfilled annotation slots.
        
        Each task has `overlap` slots. Client pays for all slots upfront.
        Refund = unfilled_slots × cost_per_slot
        
        Args:
            task_ids: List of task IDs being deleted
            cost_per_slot: Cost per single annotation slot
            overlap: Annotations per task (default: DEFAULT_OVERLAP)
            
        Returns:
            Dict with slot breakdown and refund amount
        """
        if overlap is None:
            overlap = cls.DEFAULT_OVERLAP
        
        if not task_ids:
            return {
                "tasks_total": 0,
                "overlap_per_task": overlap,
                "total_slots_charged": 0,
                "slots_filled": 0,
                "slots_unfilled": 0,
                "cost_per_slot": float(cost_per_slot),
                "refund_amount": 0,
                "per_task_breakdown": [],
            }
        
        # Get annotation counts per task
        annotation_counts = cls.get_task_annotation_slot_counts(task_ids, overlap)
        
        total_slots_charged = len(task_ids) * overlap
        slots_filled = sum(annotation_counts.values())
        slots_unfilled = total_slots_charged - slots_filled
        
        refund_amount = Decimal(str(slots_unfilled)) * cost_per_slot
        
        # Per-task breakdown
        per_task_breakdown = []
        for task_id in task_ids:
            annotations = annotation_counts.get(task_id, 0)
            refundable_slots = overlap - annotations
            per_task_breakdown.append({
                "task_id": task_id,
                "annotations": annotations,
                "refundable_slots": refundable_slots,
                "refund_amount": float(Decimal(str(refundable_slots)) * cost_per_slot),
            })
        
        return {
            "tasks_total": len(task_ids),
            "overlap_per_task": overlap,
            "total_slots_charged": total_slots_charged,
            "slots_filled": slots_filled,
            "slots_unfilled": slots_unfilled,
            "cost_per_slot": float(cost_per_slot),
            "refund_amount": float(refund_amount.quantize(Decimal('0.01'))),
            "per_task_breakdown": per_task_breakdown,
        }
    
    @classmethod
    def calculate_project_slot_stats(cls, project, overlap: int = None) -> Dict:
        """
        Calculate slot-based statistics for a project.
        
        Args:
            project: Project instance
            overlap: Annotations per task (default: DEFAULT_OVERLAP)
            
        Returns:
            Dict with slot statistics for work completion calculation
        """
        from tasks.models import Task, Annotation
        from django.db.models import Count
        
        if overlap is None:
            overlap = cls.DEFAULT_OVERLAP
        
        # Get all task IDs
        task_ids = list(project.tasks.values_list('id', flat=True))
        total_tasks = len(task_ids)
        
        if total_tasks == 0:
            return {
                "total_tasks": 0,
                "overlap_per_task": overlap,
                "total_slots": 0,
                "filled_slots": 0,
                "unfilled_slots": 0,
                "work_completion_percentage": 0,
            }
        
        # Get annotation counts per task, capped at overlap
        annotation_counts = cls.get_task_annotation_slot_counts(task_ids, overlap)
        
        total_slots = total_tasks * overlap
        filled_slots = sum(annotation_counts.values())
        unfilled_slots = total_slots - filled_slots
        work_completion = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "overlap_per_task": overlap,
            "total_slots": total_slots,
            "filled_slots": filled_slots,
            "unfilled_slots": unfilled_slots,
            "work_completion_percentage": round(work_completion, 2),
        }

