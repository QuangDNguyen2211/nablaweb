# Generated by Django 3.1.7 on 2021-04-13 13:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_auto_20210413_1346"),
        ("vote", "0003_auto_20210210_2135"),
    ]

    operations = [
        migrations.AddField(
            model_name="votingevent",
            name="eligible_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="voting_events",
                to="accounts.nablagroup",
            ),
        ),
    ]
