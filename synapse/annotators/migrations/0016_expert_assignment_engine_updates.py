# Generated manually for expert assignment engine updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotators', '0015_add_activity_tracking_fields'),
    ]

    operations = [
        # Add activity tracking fields to ExpertProfile
        migrations.AddField(
            model_name='expertprofile',
            name='is_active_for_assignments',
            field=models.BooleanField(
                default=True,
                help_text='Whether expert is currently active for receiving new reviews'
            ),
        ),
        migrations.AddField(
            model_name='expertprofile',
            name='inactive_since',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='When expert was marked inactive (for timeout handling)'
            ),
        ),
        # Rename max_reviews_per_day to max_concurrent_reviews
        migrations.RenameField(
            model_name='expertprofile',
            old_name='max_reviews_per_day',
            new_name='max_concurrent_reviews',
        ),
        # Remove expertise_level field (no longer needed)
        migrations.RemoveField(
            model_name='expertprofile',
            name='expertise_level',
        ),
    ]
