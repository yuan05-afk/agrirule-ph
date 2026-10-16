# Generated manually for classroom baseline.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Consultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.CharField(choices=[('wet', 'Wet'), ('dry', 'Dry')], max_length=20)),
                ('soil_type', models.CharField(choices=[('clay', 'Clay'), ('loam', 'Loam'), ('sandy', 'Sandy'), ('silt', 'Silt')], max_length=20)),
                ('water_availability', models.CharField(choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')], max_length=20)),
                ('farm_type', models.CharField(choices=[('irrigated', 'Irrigated'), ('rainfed', 'Rainfed')], max_length=20)),
                ('soil_ph_category', models.CharField(choices=[('acidic', 'Acidic'), ('neutral', 'Neutral'), ('alkaline', 'Alkaline')], max_length=20)),
                ('budget_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], max_length=20)),
                ('crop_preference', models.CharField(choices=[('staple', 'Staple'), ('vegetable', 'Vegetable'), ('resilient', 'Resilient Crop')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Crop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('category', models.CharField(choices=[('staples_root', 'Staples, Legumes, and Root Crops'), ('industrial_perennial', 'Industrial and Perennial Crops'), ('fruit', 'Fruit Crops'), ('vegetable_spice', 'Vegetables and Spices')], max_length=40)),
                ('description', models.TextField(blank=True)),
                ('planting_note', models.TextField(blank=True)),
                ('avoid_note', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('season_condition', models.CharField(blank=True, choices=[('wet', 'Wet'), ('dry', 'Dry')], max_length=20)),
                ('soil_type_condition', models.CharField(blank=True, choices=[('clay', 'Clay'), ('loam', 'Loam'), ('sandy', 'Sandy'), ('silt', 'Silt')], max_length=20)),
                ('water_availability_condition', models.CharField(blank=True, choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')], max_length=20)),
                ('farm_type_condition', models.CharField(blank=True, choices=[('irrigated', 'Irrigated'), ('rainfed', 'Rainfed')], max_length=20)),
                ('soil_ph_condition', models.CharField(blank=True, choices=[('acidic', 'Acidic'), ('neutral', 'Neutral'), ('alkaline', 'Alkaline')], max_length=20)),
                ('budget_level_condition', models.CharField(blank=True, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], max_length=20)),
                ('crop_preference_condition', models.CharField(blank=True, choices=[('staple', 'Staple'), ('vegetable', 'Vegetable'), ('resilient', 'Resilient Crop')], max_length=20)),
                ('score', models.IntegerField()),
                ('rule_type', models.CharField(choices=[('positive', 'Positive'), ('negative', 'Negative'), ('avoid', 'Avoid')], default='positive', max_length=20)),
                ('explanation', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='expert_system.crop')),
            ],
            options={'ordering': ['crop__name', 'name']},
        ),
        migrations.CreateModel(
            name='ConsultationResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('explanation_text', models.TextField(blank=True)),
                ('is_recommended', models.BooleanField(default=False)),
                ('is_avoid', models.BooleanField(default=False)),
                ('rank_order', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('consultation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='expert_system.consultation')),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expert_system.crop')),
            ],
            options={'ordering': ['rank_order', '-score', 'crop__name'], 'unique_together': {('consultation', 'crop')}},
        ),
    ]
