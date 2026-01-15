"""
Management command to encrypt existing data in the database.

This command encrypts existing unencrypted data in sensitive fields:
- Task.data, Task.meta
- Annotation.result, Annotation.prediction
- AnnotationDraft.result
- Prediction.result

Usage:
    python manage.py encrypt_existing_data --dry-run  # Preview what will be encrypted
    python manage.py encrypt_existing_data            # Actually encrypt data
    python manage.py encrypt_existing_data --batch-size=500  # Custom batch size
"""

import json
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from core.encryption import EncryptionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Encrypt existing unencrypted data in the database"

    # Prefix used to identify encrypted values
    ENCRYPTED_PREFIX = "enc::"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be encrypted without making changes",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of records to process per batch (default: 100)",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="all",
            choices=["all", "task", "annotation", "draft", "prediction"],
            help="Which model to encrypt (default: all)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        model_choice = options["model"]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🔐 ENCRYPTING EXISTING DATA")
        if dry_run:
            self.stdout.write(
                self.style.WARNING("   [DRY RUN - No changes will be made]")
            )
        self.stdout.write("=" * 60 + "\n")

        total_encrypted = 0

        if model_choice in ["all", "task"]:
            count = self.encrypt_tasks(batch_size, dry_run)
            total_encrypted += count

        if model_choice in ["all", "annotation"]:
            count = self.encrypt_annotations(batch_size, dry_run)
            total_encrypted += count

        if model_choice in ["all", "draft"]:
            count = self.encrypt_drafts(batch_size, dry_run)
            total_encrypted += count

        if model_choice in ["all", "prediction"]:
            count = self.encrypt_predictions(batch_size, dry_run)
            total_encrypted += count

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would encrypt {total_encrypted} fields")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Encrypted {total_encrypted} fields"))
        self.stdout.write("=" * 60 + "\n")

    def is_encrypted(self, value) -> bool:
        """Check if a value is already encrypted"""
        if isinstance(value, str):
            return value.startswith(self.ENCRYPTED_PREFIX)
        return False

    def encrypt_json_field(self, value) -> str:
        """Encrypt a JSON value and return encrypted string"""
        if value is None:
            return None

        # Serialize to JSON if it's not already a string
        if not isinstance(value, str):
            try:
                json_str = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError):
                json_str = str(value)
        else:
            json_str = value

        # Encrypt
        encrypted = EncryptionService.encrypt_field(json_str)
        return f"{self.ENCRYPTED_PREFIX}{encrypted}"

    def encrypt_tasks(self, batch_size, dry_run) -> int:
        """Encrypt Task.data and Task.meta fields"""
        from tasks.models import Task

        self.stdout.write("\n📋 Processing Tasks...")

        encrypted_count = 0
        tasks = Task.objects.all().iterator(chunk_size=batch_size)

        batch = []
        for task in tasks:
            modified = False

            # Check and encrypt data field
            if task.data and not self.is_encrypted(
                task.data if isinstance(task.data, str) else ""
            ):
                if not dry_run:
                    task.data = self.encrypt_json_field(task.data)
                modified = True
                encrypted_count += 1

            # Check and encrypt meta field
            if task.meta and not self.is_encrypted(
                task.meta if isinstance(task.meta, str) else ""
            ):
                if not dry_run:
                    task.meta = self.encrypt_json_field(task.meta)
                modified = True
                encrypted_count += 1

            if modified and not dry_run:
                batch.append(task)
                if len(batch) >= batch_size:
                    self._save_batch(batch, ["data", "meta"])
                    batch = []

        # Save remaining batch
        if batch and not dry_run:
            self._save_batch(batch, ["data", "meta"])

        self.stdout.write(
            f"   {'Would encrypt' if dry_run else 'Encrypted'}: {encrypted_count} Task fields"
        )
        return encrypted_count

    def encrypt_annotations(self, batch_size, dry_run) -> int:
        """Encrypt Annotation.result and Annotation.prediction fields"""
        from tasks.models import Annotation

        self.stdout.write("\n📝 Processing Annotations...")

        encrypted_count = 0
        annotations = Annotation.objects.all().iterator(chunk_size=batch_size)

        batch = []
        for annotation in annotations:
            modified = False

            # Check and encrypt result field
            if annotation.result and not self.is_encrypted(
                annotation.result if isinstance(annotation.result, str) else ""
            ):
                if not dry_run:
                    annotation.result = self.encrypt_json_field(annotation.result)
                modified = True
                encrypted_count += 1

            # Check and encrypt prediction field
            if annotation.prediction and not self.is_encrypted(
                annotation.prediction if isinstance(annotation.prediction, str) else ""
            ):
                if not dry_run:
                    annotation.prediction = self.encrypt_json_field(
                        annotation.prediction
                    )
                modified = True
                encrypted_count += 1

            if modified and not dry_run:
                batch.append(annotation)
                if len(batch) >= batch_size:
                    self._save_batch(batch, ["result", "prediction"])
                    batch = []

        # Save remaining batch
        if batch and not dry_run:
            self._save_batch(batch, ["result", "prediction"])

        self.stdout.write(
            f"   {'Would encrypt' if dry_run else 'Encrypted'}: {encrypted_count} Annotation fields"
        )
        return encrypted_count

    def encrypt_drafts(self, batch_size, dry_run) -> int:
        """Encrypt AnnotationDraft.result field"""
        from tasks.models import AnnotationDraft

        self.stdout.write("\n📄 Processing Annotation Drafts...")

        encrypted_count = 0
        drafts = AnnotationDraft.objects.all().iterator(chunk_size=batch_size)

        batch = []
        for draft in drafts:
            if draft.result and not self.is_encrypted(
                draft.result if isinstance(draft.result, str) else ""
            ):
                if not dry_run:
                    draft.result = self.encrypt_json_field(draft.result)
                encrypted_count += 1
                batch.append(draft)
                if len(batch) >= batch_size:
                    self._save_batch(batch, ["result"])
                    batch = []

        if batch and not dry_run:
            self._save_batch(batch, ["result"])

        self.stdout.write(
            f"   {'Would encrypt' if dry_run else 'Encrypted'}: {encrypted_count} Draft fields"
        )
        return encrypted_count

    def encrypt_predictions(self, batch_size, dry_run) -> int:
        """Encrypt Prediction.result field"""
        from tasks.models import Prediction

        self.stdout.write("\n🤖 Processing Predictions...")

        encrypted_count = 0
        predictions = Prediction.objects.all().iterator(chunk_size=batch_size)

        batch = []
        for prediction in predictions:
            if prediction.result and not self.is_encrypted(
                prediction.result if isinstance(prediction.result, str) else ""
            ):
                if not dry_run:
                    prediction.result = self.encrypt_json_field(prediction.result)
                encrypted_count += 1
                batch.append(prediction)
                if len(batch) >= batch_size:
                    self._save_batch(batch, ["result"])
                    batch = []

        if batch and not dry_run:
            self._save_batch(batch, ["result"])

        self.stdout.write(
            f"   {'Would encrypt' if dry_run else 'Encrypted'}: {encrypted_count} Prediction fields"
        )
        return encrypted_count

    def _save_batch(self, batch, fields):
        """Save a batch of objects efficiently"""
        if not batch:
            return

        model_class = type(batch[0])
        try:
            with transaction.atomic():
                model_class.objects.bulk_update(batch, fields)
            self.stdout.write(f"   ✓ Saved batch of {len(batch)} records")
        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
            self.stdout.write(self.style.ERROR(f"   ✗ Failed to save batch: {e}"))
