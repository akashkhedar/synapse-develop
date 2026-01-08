# Generated migration for accuracy and performance tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("annotators", "0011_add_expert_payment_fields"),
        ("tasks", "0001_initial"),  # Assuming tasks has an initial migration
    ]

    operations = [
        # Add accuracy fields to TaskAssignment
        migrations.AddField(
            model_name="taskassignment",
            name="ground_truth_accuracy",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Accuracy against ground truth (0-100)",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="taskassignment",
            name="accuracy_level",
            field=models.CharField(
                blank=True,
                help_text="Accuracy classification (excellent, good, acceptable, poor, very_poor)",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="taskassignment",
            name="accuracy_bonus_multiplier",
            field=models.DecimalField(
                decimal_places=2,
                default=1.0,
                help_text="Bonus/penalty multiplier based on accuracy",
                max_digits=4,
            ),
        ),
        # Add ground truth accuracy tracking to TrustLevel
        migrations.AddField(
            model_name="trustlevel",
            name="ground_truth_evaluations",
            field=models.IntegerField(
                default=0, help_text="Number of times compared against ground truth"
            ),
        ),
        migrations.AddField(
            model_name="trustlevel",
            name="accuracy_history",
            field=models.JSONField(
                blank=True, help_text="Recent accuracy scores", null=True
            ),
        ),
        migrations.AddField(
            model_name="trustlevel",
            name="last_accuracy_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Create AnnotatorPerformanceHistory model
        migrations.CreateModel(
            name="AnnotatorPerformanceHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("ground_truth_accuracy", "Ground Truth Accuracy"),
                            ("honeypot_accuracy", "Honeypot Accuracy"),
                            ("peer_agreement", "Peer Agreement"),
                            ("level_change", "Trust Level Change"),
                            ("fraud_flag", "Fraud Flag"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "old_value",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "new_value",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("change_reason", models.TextField(blank=True)),
                ("details", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "annotator",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="performance_history",
                        to="annotators.annotatorprofile",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="+",
                        to="tasks.task",
                    ),
                ),
            ],
            options={
                "verbose_name": "Annotator Performance History",
                "verbose_name_plural": "Annotator Performance Histories",
                "db_table": "annotator_performance_history",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="annotatorperformancehistory",
            index=models.Index(
                fields=["annotator", "-created_at"],
                name="annotator_p_annotat_7b8c12_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="annotatorperformancehistory",
            index=models.Index(
                fields=["metric_type", "-created_at"],
                name="annotator_p_metric__a4e3f2_idx",
            ),
        ),
    ]





