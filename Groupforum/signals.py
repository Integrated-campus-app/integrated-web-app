from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Answer, Comment, Notification

@receiver(post_save, sender=Answer)
def notify_new_answer(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'notifications',
            {
                'type': 'notify',
                'message': f'New answer: {instance.text[:50]}...'
            }
        )

@receiver(post_save, sender=Comment)
def notify_answer_author(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            message=f"New comment on your answer",
            anonymous_id=instance.answer.anonymous_id
        )