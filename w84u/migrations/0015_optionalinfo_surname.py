# Generated by Django 5.0.6 on 2024-08-04 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('w84u', '0014_alter_customuser_more_info_alter_optionalinfo_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='optionalinfo',
            name='surname',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
