# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-06 12:18
from __future__ import unicode_literals

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import image_cropping.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jobs", "0003_auto_20170920_1429"),
    ]

    operations = [
        migrations.AddField(
            model_name="advert",
            name="body",
            field=models.TextField(
                blank=True,
                help_text='Vises kun i artikkelen. Man kan her bruke <a href="http://en.wikipedia.org/wiki/Markdown" target="_blank">markdown</a> for å formatere teksten.',
                verbose_name="brødtekst",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="advert_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Opprettet av",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="created_date",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Publiseringsdato"
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="cropping",
            field=image_cropping.fields.ImageRatioField(
                "picture",
                "770x300",
                adapt_rotation=False,
                allow_fullsize=False,
                free_crop=False,
                help_text=None,
                hide_image_field=False,
                size_warning=False,
                verbose_name="Beskjæring",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="headline",
            field=models.CharField(blank=True, max_length=100, verbose_name="tittel"),
        ),
        migrations.AddField(
            model_name="advert",
            name="last_changed_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="advert_edited",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Endret av",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="last_changed_date",
            field=models.DateTimeField(
                blank=True,
                default=django.utils.timezone.now,
                null=True,
                verbose_name="Redigeringsdato",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="lead_paragraph",
            field=models.TextField(
                blank=True,
                help_text="Vises på forsiden og i artikkelen",
                verbose_name="ingress",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="picture",
            field=models.ImageField(
                blank=True,
                help_text="Bilder som er større enn 770x300 px ser best ut. Du kan beskjære bildet etter opplasting.",
                null=True,
                upload_to="uploads/news_pictures",
                verbose_name="Bilde",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="publication_date",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Publikasjonstid"
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="published",
            field=models.NullBooleanField(
                default=True,
                help_text="Dato har høyere prioritet enn dette feltet.",
                verbose_name="Publisert",
            ),
        ),
        migrations.AddField(
            model_name="advert",
            name="slug",
            field=models.SlugField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="advert",
            name="view_counter",
            field=models.IntegerField(
                default=0, editable=False, verbose_name="Visninger"
            ),
        ),
        migrations.AlterField(
            model_name="advert",
            name="news_ptr",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                serialize=False,
                to="news.News",
            ),
        ),
    ]
