from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from abilityhub.models import Person, Image, Chat, Message, Transaction, Deposit
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from freezegun import freeze_time
import os

class PersonModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.person = Person.objects.create(user = cls.user)
    
    def test_person_creation(self):
        self.assertEqual(self.person.user, self.user)
        self.assertEqual(self.person.credits, 0)
        self.assertEqual(self.person.description, 'Hello, this is my description!')

    # delete() tested in the next class

    def test_str_method(self):
        self.assertEqual(str(self.person), 'John Korho')
    
    def test_description_max_length(self):
        max_length = self.person._meta.get_field('description').max_length
        self.assertEqual(max_length, 500)
    
    def test_user_on_delete(self):
        person_id = self.person.id
        self.user.delete()
        self.assertFalse(Person.objects.filter(id=person_id).exists())

class PersonModelDeletionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.user2 = User.objects.create(
            username = 'olafvirta',
            first_name = 'Olaf',
            last_name = 'Virta'
        )
        cls.person1 = Person.objects.create(user = cls.user1)
        cls.person2 = Person.objects.create(user = cls.user2)
        cls.chat = Chat.objects.create()
        cls.chat.participants.add(cls.person1, cls.person2)
        cls.message = Message.objects.create(
            chat = cls.chat,
            sender = cls.person1,
            content = "Hello Olaf! It's me, John."
        )
        cls.transaction = Transaction.objects.create(
            sender = cls.person1,
            receiver = cls.person2,
            sender_credits_after = 3,
            receiver_credits_after = 7,
            sent_credits = 1
        )
        cls.deposit = Deposit.objects.create(
            depositor = cls.person1,
            payment_method = 'credit_card',
            added_credits = 3,
            depositor_credits_after = 5
        )

    def test_chat_cascade(self):
        chat_id = self.chat.id
        self.person1.delete()
        self.assertTrue(Chat.objects.filter(id=chat_id).exists())
        self.person2.delete()
        self.assertFalse(Chat.objects.filter(id=chat_id).exists())
    
    def test_message_set_null(self):
        self.person1.delete()
        self.message.refresh_from_db()
        self.assertIsNone(self.message.sender)
    
    def test_transaction_set_null_and_cascade_sender_first(self):
        transaction_id = self.transaction.id
        self.person1.delete()
        self.assertTrue(Transaction.objects.filter(id=transaction_id).exists())
        self.transaction.refresh_from_db()
        self.assertIsNone(self.transaction.sender)
        self.person2.delete()
        self.assertFalse(Transaction.objects.filter(id=transaction_id).exists())

    def test_transaction_set_null_and_cascade_receiver_first(self):
        transaction_id = self.transaction.id
        self.person2.delete()
        self.assertTrue(Transaction.objects.filter(id=transaction_id).exists())
        self.transaction.refresh_from_db()
        self.assertIsNone(self.transaction.receiver)
        self.person1.delete()
        self.assertFalse(Transaction.objects.filter(id=transaction_id).exists())
    
    def test_deposit_cascade(self):
        deposit_id = self.deposit.id
        self.person1.delete()
        self.assertFalse(Deposit.objects.filter(id=deposit_id).exists())

class ImageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.person = Person.objects.create(user = cls.user)
        cls.image_rep = SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg')
        cls.image = Image.objects.create(
            uploader = cls.person,
            title = 'Test Image',
            image = cls.image_rep
        )

    def test_image_creation(self):
        self.assertEqual(self.image.uploader, self.person)
        self.assertEqual(self.image.title, 'Test Image')
        self.assertFalse(self.image.is_private)

    def test_title_max_length(self):
        max_length = self.image._meta.get_field('title').max_length
        self.assertEqual(max_length, 50)

    def test_delete_method(self):
        image_path = self.image.image.path
        self.image.delete()
        self.assertFalse(os.path.isfile(image_path))

    def test_str_method(self):
        self.assertEqual(str(self.image), 'Image titled "Test Image", uploaded by John Korho')
    
    def test_uploader_on_delete(self):
        image_id = self.image.id
        self.person.delete()
        self.assertFalse(Image.objects.filter(id=image_id).exists())

class ChatModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.user2 = User.objects.create(
            username = 'olafvirta',
            first_name = 'Olaf',
            last_name = 'Virta'
        )
        cls.person1 = Person.objects.create(user = cls.user1)
        cls.person2 = Person.objects.create(user = cls.user2)
        cls.chat = Chat.objects.create()
        cls.chat.participants.add(cls.person1, cls.person2)
        cls.message = Message.objects.create(
            chat = cls.chat,
            sender = cls.person1,
            content = "Hello Olaf! It's me, John."
        )
    
    def test_chat_creation(self):
        actual_participants = set(self.chat.participants.all())
        expected_participants = {self.person1, self.person2}
        self.assertEqual(actual_participants, expected_participants)
        self.assertIn(self.chat, self.person1.chats.all())
        self.assertIn(self.chat, self.person2.chats.all())
        now = timezone.now()
        self.assertAlmostEqual(self.chat.updated_at, now, delta=timezone.timedelta(seconds=1))
    
    def test_message_deletion(self):
        message_id = self.message.id
        self.chat.delete()
        self.assertFalse(Message.objects.filter(id=message_id).exists())

    def test_str_method(self):
        self.assertEqual(str(self.chat), 'Chat between John Korho, Olaf Virta')

class MessageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.user2 = User.objects.create(
            username = 'olafvirta',
            first_name = 'Olaf',
            last_name = 'Virta'
        )
        cls.person1 = Person.objects.create(user = cls.user1)
        cls.person2 = Person.objects.create(user = cls.user2)
        cls.chat = Chat.objects.create()
        cls.chat.participants.add(cls.person1, cls.person2)
        cls.message = Message.objects.create(
            chat = cls.chat,
            sender = cls.person1,
            content = "Hello Olaf! It's me, John."
        )

    def test_message_creation(self):
        self.assertEqual(self.message.chat, self.chat)
        self.assertIn(self.message, self.chat.messages.all())
        self.assertEqual(self.message.sender, self.person1)
        self.assertIn(self.message, self.person1.sent_messages.all())
        self.assertEqual(self.message.content, "Hello Olaf! It's me, John.")
        now = timezone.now()
        self.assertAlmostEqual(self.message.timestamp, now, delta=timezone.timedelta(seconds=1))

    @freeze_time("2024-09-21 12:00:00")
    def test_str_method(self):
        message = Message.objects.create(
            chat = self.chat,
            sender = self.person1,
            content = "Hello Olaf! It's me, John."
        )
        expected_str = f'Message from {self.person1} to {self.person2} at 2024-09-21 12:00:00+00:00'
        self.assertEqual(str(message), expected_str)

class TransactionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.user2 = User.objects.create(
            username = 'olafvirta',
            first_name = 'Olaf',
            last_name = 'Virta'
        )
        cls.person1 = Person.objects.create(user = cls.user1)
        cls.person2 = Person.objects.create(user = cls.user2)
        cls.transaction = Transaction.objects.create(
            sender = cls.person1,
            receiver = cls.person2,
            sender_credits_after = 3,
            receiver_credits_after = 1,
            sent_credits = 2
        )
    
    def test_transaction_creation(self):
        self.assertEqual(self.transaction.sender, self.person1)
        self.assertEqual(self.transaction.receiver, self.person2)
        self.assertEqual(self.transaction.sender_credits_after, 3)
        self.assertEqual(self.transaction.receiver_credits_after, 1)
        self.assertEqual(self.transaction.sent_credits, 2)
        now = timezone.now()
        self.assertAlmostEqual(self.transaction.timestamp, now, delta=timezone.timedelta(seconds=1))
    
    @freeze_time("2024-09-21 12:00:00")
    def test_str_method(self):
        transaction = Transaction.objects.create(
            sender = self.person1,
            receiver = self.person2,
            sender_credits_after = 3,
            receiver_credits_after = 1,
            sent_credits = 2
        )
        expected_str = f'Transaction from {self.person1} to {self.person2} at 2024-09-21 12:00:00+00:00'
        self.assertEqual(str(transaction), expected_str)

class DepositModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(
            username = 'johnkorho',
            first_name = 'John',
            last_name = 'Korho'
        )
        cls.person1 = Person.objects.create(user = cls.user1)
        cls.deposit = Deposit.objects.create(
            depositor = cls.person1,
            payment_method = 'credit_card',
            added_credits = 3,
            depositor_credits_after = 5
        )
    
    def test_deposit_creation(self):
        self.assertEqual(self.deposit.depositor, self.person1)
        self.assertEqual(self.deposit.payment_method, 'credit_card')
        self.assertEqual(self.deposit.added_credits, 3)
        self.assertEqual(self.deposit.depositor_credits_after, 5)
        now = timezone.now()
        self.assertAlmostEqual(self.deposit.timestamp, now, delta=timezone.timedelta(seconds=1))

    @freeze_time("2024-09-21 12:00:00")
    def test_str_method(self):
        deposit = Deposit.objects.create(
            depositor = self.person1,
            payment_method = 'credit_card',
            added_credits = 3,
            depositor_credits_after = 5
        )
        expected_str = f'The deposit by {self.person1} at 2024-09-21 12:00:00+00:00'
        self.assertEqual(str(deposit), expected_str)