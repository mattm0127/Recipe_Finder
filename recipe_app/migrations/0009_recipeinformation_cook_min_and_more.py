# Generated by Django 5.1.4 on 2024-12-14 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe_app', '0008_rename_api_id_recipeinformation_recipe_api_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipeinformation',
            name='cook_min',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recipeinformation',
            name='preparation_min',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
