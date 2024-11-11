from django.db import models
from django.conf import settings
import os

class Person(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True
    )
    credits = models.IntegerField(default=0)
    description = models.TextField(max_length=500, default="Hello, this is my description!")

    def delete(self, *args, **kwargs):
        for chat in self.chats.all():
            chat.participants.remove(self)
            if chat.participants.count() == 0:
                chat.delete()
        for transaction in self.sent_transactions.all():
            if transaction.receiver is None:
                transaction.delete()
        for transaction in self.received_transactions.all():
            if transaction.sender is None:
                transaction.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.user.get_full_name()
    # Known issue: created Person never gets deleted. 
    # Ideally, Person would be deleted when two conditions are met:
    # #1 when Person.user.is_active == False
    # #2 when Person is not needed in the context of any Chat or Transaction

class Image(models.Model):
    uploader = models.ForeignKey(Person, related_name='images', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    image = models.ImageField(upload_to='images/')
    is_private = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f'Image titled "{self.title}", uploaded by {self.uploader}'

class Chat(models.Model):
    # object deleted if participants.count() == 0 (see delete() of Person)
    participants = models.ManyToManyField(Person, related_name='chats')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Chat between {", ".join([str(participant) for participant in self.participants.all()])}'

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(Person, related_name='sent_messages', on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        receiver = self.chat.participants.exclude(id=self.sender.id).first()
        return f'Message from {self.sender} to {receiver} at {self.timestamp}'
    
class Transaction(models.Model):
    # object deleted if sender == None && receiver == None (see delete() of Person)
    sender = models.ForeignKey(Person, related_name='sent_transactions', on_delete=models.SET_NULL, null=True)
    receiver = models.ForeignKey(Person, related_name='received_transactions', on_delete=models.SET_NULL, null=True)
    sender_credits_after = models.IntegerField()
    receiver_credits_after = models.IntegerField()
    sent_credits = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaction from {self.sender} to {self.receiver} at {self.timestamp}'

class Deposit(models.Model):
    depositor = models.ForeignKey(Person, related_name='deposits', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    added_credits = models.IntegerField()
    depositor_credits_after = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'The deposit by {self.depositor} at {self.timestamp}'

class Log(models.Model):
    timestamp = models.CharField(max_length=50)
    interaction_id = models.CharField(max_length=50)
    application = models.CharField(max_length=50)
    code_location = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='logs', on_delete=models.CASCADE, null=True)
    event_type = models.CharField(max_length=50)
    event_code = models.CharField(max_length=50)
    levelname = models.CharField(max_length=50)
    description = models.TextField()
    json_log = models.TextField()

    def __str__(self):
        return f'Log at {self.timestamp} from {self.application}: {self.description}'
    
def get_sentinel_user():
    return None

def set_sentinel_user():
    return None