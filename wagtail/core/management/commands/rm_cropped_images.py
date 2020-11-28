import os, shutil
from django.conf import settings
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

# we check if there is a custom image model and rendition model
# if a custom image model exist we introduce a extra setting
if hasattr(settings, 'WAGTAILIMAGES_IMAGE_MODEL_RENDITION'):
    app, model = settings.WAGTAILIMAGES_IMAGE_MODEL_RENDITION.split('.')
    Rendition = apps.get_model(app, model)
else:
    from wagtail.images.models import Rendition

image_root = os.path.join(settings.MEDIA_ROOT, 'images')


class Command(BaseCommand):
    """ Command removes all compiled images. This can be handy sometimes when you move a project or want to start
    with clean slate for image renditions """

    help = 'This command will remove all cropped images.'

    def handle(self, *args, **options):
        if hasattr(settings, 'WAGTAILIMAGES_IMAGE_MODEL') and not hasattr(
                settings, 'WAGTAILIMAGES_IMAGE_MODEL_RENDITION'
        ):
            # ask user in case of a custom image model where the custom rendition model is located
            msg = ['\n',]
            msg.append('You have set WAGTAILIMAGES_IMAGE_MODEL then you also have a custom\n')
            msg.append('rendition model. Please add to your settings the custom rendition model\n')
            msg.append('by adding WAGTAILIMAGE_IMAGE_MODEL_RENDITION\n')
            raise CommandError(self.style.ERROR(''.join(msg)))

        # Getting all cropped images from database
        images = Rendition.objects.all()
        if images:
            msg = ['\n']
            msg.append(self.style.NOTICE('Location of cropped images directory that will be deleted: %(image_root)s\n' % {'image_root': image_root}))
            msg.append(self.style.WARNING('MAKE SURE THE PATH POINTS TO YOUR CROPPED IMAGES!!!\n'))
            msg.append('There are %(count)d images cropped refrenced in DB.\n' % {'count': images.count()})
            msg.append('These cropped images will be deleted by deleting the image folder.\n')
            msg.append('Don\'t worry on visiting the website they will be recreated on the fly.\n')
            msg.append('Are you sure you want to delete? yes / no: ')
            if input(''.join(msg)) == 'yes':
                # empty db from cropped images
                images.delete()
                # removing directory with cropped images
                shutil.rmtree(image_root)
                self.stdout.write(self.style.SUCCESS('All cropped images are removed'))
            else:
                self.stdout.write(self.style.NOTICE('You canceled the removal of cropped images!'))
        else:
            self.stdout.write(self.style.NOTICE('There are currently no cropped images in your project.'))
