# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-26 12:58
from __future__ import unicode_literals

from django.db import migrations


def forwards_func(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")

    Podcast = apps.get_model("podcast", "Podcast")
    HitCount = apps.get_model("hitcount", "HitCount")

    ctype = ContentType.objects.get_for_model(Podcast)
    # db_alias = schema_editor.connection.alias
    ct_article, _ = ContentType.objects.get_or_create(app_label="news", model="newsarticle")
    podcasts = Podcast.objects.all()
    for p in podcasts:
        hit_count, created = HitCount.objects.get_or_create(
            content_type=ctype, object_pk=p.pk,
        )
        if created:
            hit_count.hits = p.view_counter
            hit_count.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('podcast', '0002_auto_20170920_1318'),
        ('hitcount', '0002_index_ip_and_session'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.RemoveField(model_name='podcast', name='view_counter',),
    ]
