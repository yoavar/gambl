# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-21 13:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0002_auto_20161020_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='weather',
            field=models.CharField(max_length=200, null=True),
        ),
    ]