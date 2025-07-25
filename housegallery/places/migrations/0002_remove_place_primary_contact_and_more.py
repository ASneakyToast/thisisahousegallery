# Generated by Django 5.0.10 on 2025-07-04 06:24

import django.db.models.deletion
import modelcluster.fields
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artists', '0002_initial'),
        ('places', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='place',
            name='primary_contact',
        ),
        migrations.RemoveField(
            model_name='place',
            name='primary_link',
        ),
        migrations.AddField(
            model_name='place',
            name='links',
            field=wagtail.fields.StreamField([('links', 10)], blank=True, block_lookup={0: ('wagtail.blocks.CharBlock', (), {'help_text': 'Optional title for the list of links', 'required': False}), 1: ('wagtail.blocks.CharBlock', (), {'help_text': 'Link text to display. Leave blank to use the page/document title or URL as fallback', 'required': False}), 2: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('page', 'Page'), ('external', 'External URL'), ('document', 'Document'), ('email', 'Email Address')], 'help_text': 'Select the type of link you want to create'}), 3: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 4: ('wagtail.blocks.URLBlock', (), {'required': False}), 5: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 6: ('wagtail.blocks.EmailBlock', (), {'required': False}), 7: ('wagtail.blocks.StructBlock', [[('link_text', 1), ('link_type', 2), ('page', 3), ('external_url', 4), ('document', 5), ('email', 6)]], {'label': 'Button Style Link'}), 8: ('wagtail.blocks.StructBlock', [[('link_text', 1), ('link_type', 2), ('page', 3), ('external_url', 4), ('document', 5), ('email', 6)]], {'label': 'Carrot Style Link'}), 9: ('wagtail.blocks.StreamBlock', [[('button_link', 7), ('carrot_link', 8)]], {}), 10: ('wagtail.blocks.StructBlock', [[('title', 0), ('links', 9)]], {})}, help_text='Links related to this place (website, social media, etc.)'),
        ),
        migrations.CreateModel(
            name='PlaceMaintainer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('artist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintained_places', to='artists.artist')),
                ('place', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='place_maintainers', to='places.place')),
            ],
            options={
                'verbose_name': 'Place Maintainer',
                'verbose_name_plural': 'Place Maintainers',
                'unique_together': {('place', 'artist')},
            },
        ),
        migrations.AddField(
            model_name='place',
            name='maintainers',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='places_maintained', through='places.PlaceMaintainer', to='artists.artist'),
        ),
    ]
