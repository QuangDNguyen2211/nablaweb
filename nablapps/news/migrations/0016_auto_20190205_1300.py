# Generated by Django 2.1.5 on 2019-02-05 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0015_auto_20180922_1915"),
    ]

    operations = [
        migrations.RemoveField(model_name="newsarticle", name="publication_date",),
        migrations.RemoveField(model_name="newsarticle", name="published",),
    ]
