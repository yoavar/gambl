# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-20 17:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='match_date',
            field=models.DateTimeField(),
        ),
    ]
