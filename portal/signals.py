from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_profile_image(sender, instance, **kwargs):
    profile_image = instance.profile_image
    if profile_image:
        profile_image.delete(save=False)