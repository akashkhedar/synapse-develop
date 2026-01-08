"""
Management command to initialize annotation pricing based on the master pricing table
"""
from django.core.management.base import BaseCommand
from billing.models import AnnotationPricing


class Command(BaseCommand):
    help = 'Initialize annotation pricing rules based on master pricing table'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating annotation pricing rules...')
        
        pricing_data = [
            # 2D Images
            {
                'data_type': '2d_image',
                'modality': 'X-ray (Chest)',
                'base_credit': 1,
                'unit_description': 'per image',
                'classification_credit': 1,
                'bounding_box_credit': 5,
                'segmentation_credit': 10,
                'keypoint_credit': 8,
                'polygon_credit': 12,
            },
            {
                'data_type': '2d_image',
                'modality': 'X-ray (Extremity)',
                'base_credit': 1,
                'unit_description': 'per image',
                'classification_credit': 1,
                'bounding_box_credit': 4,
                'segmentation_credit': 8,
                'keypoint_credit': 6,
                'polygon_credit': 10,
            },
            {
                'data_type': '2d_image',
                'modality': 'Mammography',
                'base_credit': 2,
                'unit_description': 'per image',
                'classification_credit': 2,
                'bounding_box_credit': 8,
                'segmentation_credit': 15,
                'keypoint_credit': 10,
                'polygon_credit': 18,
            },
            {
                'data_type': '2d_image',
                'modality': 'Retinal Scan',
                'base_credit': 1,
                'unit_description': 'per image',
                'classification_credit': 1,
                'bounding_box_credit': 6,
                'segmentation_credit': 12,
                'keypoint_credit': 10,
                'polygon_credit': 15,
            },
            {
                'data_type': '2d_image',
                'modality': 'Skin/Dermoscopy',
                'base_credit': 1,
                'unit_description': 'per image',
                'classification_credit': 1,
                'bounding_box_credit': 5,
                'segmentation_credit': 10,
                'keypoint_credit': 8,
                'polygon_credit': 12,
            },
            {
                'data_type': '2d_image',
                'modality': 'Pathology Slide',
                'base_credit': 3,
                'unit_description': 'per image',
                'classification_credit': 3,
                'bounding_box_credit': 12,
                'segmentation_credit': 25,
                'keypoint_credit': 15,
                'polygon_credit': 30,
            },
            {
                'data_type': '2d_image',
                'modality': 'Ultrasound (Single)',
                'base_credit': 1,
                'unit_description': 'per image',
                'classification_credit': 1,
                'bounding_box_credit': 6,
                'segmentation_credit': 12,
                'keypoint_credit': 10,
                'polygon_credit': 15,
            },
            
            # 3D Volumes
            {
                'data_type': '3d_volume',
                'modality': 'CT Scan',
                'base_credit': 2,
                'unit_description': 'per slice',
                'classification_credit': 2,
                'bounding_box_credit': 10,
                'segmentation_credit': 20,
            },
            {
                'data_type': '3d_volume',
                'modality': 'MRI',
                'base_credit': 3,
                'unit_description': 'per slice',
                'classification_credit': 3,
                'bounding_box_credit': 12,
                'segmentation_credit': 25,
            },
            {
                'data_type': '3d_volume',
                'modality': 'PET-CT',
                'base_credit': 4,
                'unit_description': 'per slice',
                'classification_credit': 4,
                'bounding_box_credit': 15,
                'segmentation_credit': 30,
            },
            
            # Time Series
            {
                'data_type': 'time_series',
                'modality': 'ECG',
                'base_credit': 3,
                'unit_description': 'per 10-sec',
                'classification_credit': 3,
                'keypoint_credit': 5,
                'time_sequence_credit': 8,
            },
            {
                'data_type': 'time_series',
                'modality': 'EEG',
                'base_credit': 4,
                'unit_description': 'per 10-sec',
                'classification_credit': 4,
                'keypoint_credit': 6,
                'time_sequence_credit': 10,
            },
            {
                'data_type': 'time_series',
                'modality': 'EMG',
                'base_credit': 2,
                'unit_description': 'per 10-sec',
                'classification_credit': 2,
                'keypoint_credit': 4,
                'time_sequence_credit': 6,
            },
            {
                'data_type': 'time_series',
                'modality': 'ICU Monitor Data',
                'base_credit': 5,
                'unit_description': 'per 10-sec',
                'classification_credit': 5,
                'keypoint_credit': 8,
                'time_sequence_credit': 12,
            },
            
            # Video
            {
                'data_type': 'video',
                'modality': 'Endoscopy',
                'base_credit': 20,
                'unit_description': 'per minute',
                'classification_credit': 20,
                'bounding_box_credit': 40,
                'segmentation_credit': 80,
                'keypoint_credit': 60,
                'polygon_credit': 100,
            },
            {
                'data_type': 'video',
                'modality': 'Ultrasound Video',
                'base_credit': 15,
                'unit_description': 'per minute',
                'classification_credit': 15,
                'bounding_box_credit': 30,
                'segmentation_credit': 60,
                'keypoint_credit': 45,
                'polygon_credit': 75,
            },
            {
                'data_type': 'video',
                'modality': 'Surgical Recording',
                'base_credit': 25,
                'unit_description': 'per minute',
                'classification_credit': 25,
                'bounding_box_credit': 50,
                'segmentation_credit': 100,
                'keypoint_credit': 75,
                'polygon_credit': 125,
            },
            
            # 3D Annotations
            {
                'data_type': '3d_annotation',
                'modality': '3D Bounding Box',
                'base_credit': 0,
                'unit_description': 'per annotation',
                'bounding_box_credit': 50,
            },
            {
                'data_type': '3d_annotation',
                'modality': '3D Segmentation',
                'base_credit': 0,
                'unit_description': 'per annotation',
                'segmentation_credit': 100,
            },
            {
                'data_type': '3d_annotation',
                'modality': '3D Mesh',
                'base_credit': 0,
                'unit_description': 'per annotation',
                'polygon_credit': 150,
            },
            
            # Signal Data
            {
                'data_type': 'signal_data',
                'modality': 'Audio (Stethoscope)',
                'base_credit': 2,
                'unit_description': 'per minute',
                'classification_credit': 2,
                'time_sequence_credit': 5,
            },
            {
                'data_type': 'signal_data',
                'modality': 'Respiratory Signals',
                'base_credit': 3,
                'unit_description': 'per minute',
                'classification_credit': 3,
                'time_sequence_credit': 8,
            },
            
            # Documents
            {
                'data_type': 'document',
                'modality': 'Medical Report',
                'base_credit': 0.5,
                'unit_description': 'per page',
                'classification_credit': 0.5,
                'bounding_box_credit': 2,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for pricing in pricing_data:
            obj, created = AnnotationPricing.objects.update_or_create(
                data_type=pricing['data_type'],
                modality=pricing['modality'],
                defaults=pricing
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created: {obj.get_data_type_display()} - {obj.modality}'
                ))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {obj.get_data_type_display()} - {obj.modality}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully initialized pricing: {created_count} created, {updated_count} updated'
        ))





