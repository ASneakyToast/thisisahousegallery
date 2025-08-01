# Generated by Django 5.0.10 on 2025-07-17 20:51

from django.db import migrations


def migrate_exhibition_images(apps, schema_editor):
    """Transfer existing ExhibitionImage records to new separate models"""
    ExhibitionImage = apps.get_model('exhibitions', 'ExhibitionImage')
    InstallationPhoto = apps.get_model('exhibitions', 'InstallationPhoto')
    OpeningReceptionPhoto = apps.get_model('exhibitions', 'OpeningReceptionPhoto')
    ShowcardPhoto = apps.get_model('exhibitions', 'ShowcardPhoto')
    InProgressPhoto = apps.get_model('exhibitions', 'InProgressPhoto')
    
    # Map image types to their corresponding models
    type_model_map = {
        'exhibition': InstallationPhoto,
        'opening': OpeningReceptionPhoto,
        'showcards': ShowcardPhoto,
        'in_progress': InProgressPhoto,
    }
    
    # Process each existing ExhibitionImage record
    for old_image in ExhibitionImage.objects.all():
        model_class = type_model_map.get(old_image.image_type)
        if model_class:
            new_image = model_class(
                page=old_image.page,
                image=old_image.image,
                sort_order=old_image.sort_order,
            )
            
            # Only InstallationPhoto has related_artwork field
            if model_class == InstallationPhoto:
                new_image.related_artwork = old_image.related_artwork
            
            new_image.save()


def reverse_migrate_exhibition_images(apps, schema_editor):
    """Reverse migration - transfer back to ExhibitionImage"""
    ExhibitionImage = apps.get_model('exhibitions', 'ExhibitionImage')
    InstallationPhoto = apps.get_model('exhibitions', 'InstallationPhoto')
    OpeningReceptionPhoto = apps.get_model('exhibitions', 'OpeningReceptionPhoto')
    ShowcardPhoto = apps.get_model('exhibitions', 'ShowcardPhoto')
    InProgressPhoto = apps.get_model('exhibitions', 'InProgressPhoto')
    
    # Map models back to their image types
    model_type_map = {
        InstallationPhoto: 'exhibition',
        OpeningReceptionPhoto: 'opening',
        ShowcardPhoto: 'showcards',
        InProgressPhoto: 'in_progress',
    }
    
    # Process each new model back to ExhibitionImage
    for model_class, image_type in model_type_map.items():
        for new_image in model_class.objects.all():
            old_image = ExhibitionImage(
                page=new_image.page,
                image=new_image.image,
                image_type=image_type,
                sort_order=new_image.sort_order,
                caption='',  # Caption field was removed
            )
            
            # Only installation photos have related_artwork
            if hasattr(new_image, 'related_artwork'):
                old_image.related_artwork = new_image.related_artwork
            
            old_image.save()


class Migration(migrations.Migration):

    dependencies = [
        ('exhibitions', '0011_alter_exhibitionimage_image_type_inprogressphoto_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_exhibition_images, reverse_migrate_exhibition_images),
    ]
