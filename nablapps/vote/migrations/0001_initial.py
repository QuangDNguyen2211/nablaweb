# Generated by Django 3.0.7 on 2021-01-29 09:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Votation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=False, verbose_name='Åpen for avtemning?')),
                ('created_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Votation_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Opprettet av')),
                ('users_voted', models.ManyToManyField(related_name='users_voted', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Alternative',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('votes', models.IntegerField(default=0, verbose_name='Antall stemmer')),
                ('votation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alternatives', to='vote.Votation')),
            ],
        ),
    ]
