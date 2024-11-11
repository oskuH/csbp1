from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver
from .models import Person, Chat, Transaction

@receiver(post_delete, sender=Person)
def delete_orphan_transactions(sender, instance, **kwargs):
    for transaction in instance.sent_transactions.all():
        if transaction.receiver is None:
            transaction.delete()
    
    for transaction in instance.received_transactions.all():
        if transaction.sender is None:
            transaction.delete()