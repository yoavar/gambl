# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-10-23 15:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0003_auto_20161021_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_type', models.CharField(max_length=50)),
                ('related_obj', models.CharField(max_length=50, null=True)),
                ('data_info', models.CharField(max_length=50, null=True)),
                ('data', models.CharField(max_length=1000, null=True)),
            ],
        ),
    ]
