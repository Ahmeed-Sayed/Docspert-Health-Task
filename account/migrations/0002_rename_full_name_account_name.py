# Generated by Django 5.0.3 on 2024-07-18 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='full_name',
            new_name='name',
        ),
    ]
