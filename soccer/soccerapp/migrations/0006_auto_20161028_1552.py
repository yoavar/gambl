# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-28 15:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0005_auto_20161025_1809'),
    ]

    operations = [
        migrations.CreateModel(
            name='BetMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
                ('bookie_name', models.CharField(max_length=50, null=True)),
                ('value', models.FloatField()),
            ],
        ),
        migrations.AlterField(
            model_name='match',
            name='minutes_played',
            field=models.IntegerField(default=90),
        ),
        migrations.AddField(
            model_name='betmatch',
            name='match',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bets', to='soccerapp.Match'),
        ),
        migrations.AlterUniqueTogether(
            name='betmatch',
            unique_together=set([('match', 'type', 'bookie_name')]),
        ),
    ]