from itertools import chain
from django.db.models import Q, Value, CharField
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password, password_validators_help_texts
from .forms import UserRegistrationForm, ImageForm, MessageForm, DepositForm, DescriptionForm, SendForm
from django.db import transaction
import json

import logging
logger = logging.getLogger("custom_logger")
APPLICATION_IDENTIFIER = 'abilityhub'

from .models import Person, Image, Transaction, Chat, Message, Deposit

# needed to cause FLAW 1
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# needed to fix FLAW 4
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError

# Security Logging and Monitoring Failures (fix)
""" class ExtendedLoginView(LoginView):
    def form_invalid(self, form):
        if form.errors:
            request = self.request
            error_json = form.errors.as_json()
            error_dict = json.loads(error_json)
            
            for field, errors in error_dict.items():
                for error in errors:
                    error_message = error['message']
                    logger.warning(f'Form error in {field}: {error_message}', extra={
                        'interaction_id': request.interaction_id,
                        'application': APPLICATION_IDENTIFIER,
                        'code_location': self.__class__.__name__,
                        'user': None,
                        'event_type': 'validation_error',
                        'event_code': error['code'],
                        'description': 'Failed login attempt.'
                })

        return super().form_invalid(form) """

# Identification and Authentication Failures (fixes commented)
class RegisterView(generic.TemplateView):
    template_name = 'registration/register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form', UserRegistrationForm())
        # context['password_help_texts'] = password_validators_help_texts()
        return context
    
    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            
            """ try:
                validate_password(password)
            except ValidationError as errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, self.template_name, self.get_context_data(form=form)) """

            user = User.objects.create_user(
                username = form.cleaned_data['username'],
                password = password,
                first_name = form.cleaned_data['first_name'],
                last_name = form.cleaned_data['last_name']
            )
            Person.objects.create(user=user)
            login(request, user)
            return redirect('abilityhub:home')

        return render(request, self.template_name, self.get_context_data(form=form))

@login_required
def navbar(request):
    return render(request, 'abilityhub/navbar.html')

class HomePageView(LoginRequiredMixin, generic.ListView):
    template_name = 'abilityhub/home.html'
    context_object_name = 'other_people'

    def get_queryset(self):
        return Person.objects.exclude(user = self.request.user)
    
    def post(self, request, *args, **kwargs):
        selected_person_id = request.POST.get('person_id')
        return redirect('abilityhub:profile', pk=selected_person_id)      

# Broken Access Control
@login_required
def showMyProfile(request, pk):
    request.session['my_profile'] = True
    return redirect('abilityhub:profile', pk=pk)

class ProfileView(LoginRequiredMixin, generic.DetailView):
    model = Person
    # template_name = 'abilityhub/profile.html'
    # Broken Access Control
    def get_template_names(self):
        my_profile = self.request.session.get('my_profile', False)
        self.request.session['my_profile'] = False

        if my_profile:
            return ['abilityhub/myprofile.html']
        else:
            return ['abilityhub/otherprofile.html']

    # Since the poor CSRF-susceptible SendView is a TemplateView, send.html is served the receiver's name via sessions.
    # It is expected that SendView is accessed via another person's profile so this is where sessions gets updated.
    # This is a very poor implementation that does not account for the user directly accessing send.html via a url.
    # In fact, this get() becomes harmlessly redundant after fixing FLAW 1.
    def get(self, request, *args, **kwargs):
        person = self.get_object()
        request.session['person'] = person.id
        return super().get(request, *args, **kwargs)

@login_required
def setImagePrivacy(request, image_id):
    image = get_object_or_404(Image, id=image_id)
    image.is_private = not image.is_private
    image.save()
    auth_person = request.user.person
    return redirect('abilityhub:myprofile', pk=auth_person.id)

@login_required
def deleteImage(request, image_id):
    image = Image.objects.get(id = image_id)
    image.delete()
    auth_person = request.user.person
    return redirect('abilityhub:myprofile', pk=auth_person.id)

class UploadView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'abilityhub/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ImageForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            auth_person = request.user.person
            Image.objects.create(
                uploader = auth_person,
                title = form.cleaned_data['title'],
                image = form.cleaned_data['image']
            )
            return redirect('abilityhub:myprofile', pk=auth_person.id)
        return render(request, self.template_name, self.get_context_data(form=form))

class MessagesView(LoginRequiredMixin, generic.ListView):
    template_name = 'abilityhub/messages.html'
    context_object_name = 'chats'

    def get_queryset(self):
        auth_person = get_object_or_404(Person, user=self.request.user)
        return Chat.objects.filter(participants = auth_person)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_id = self.kwargs.get('pk')
        if chat_id:
            context['selected_chat'] = Chat.objects.get(pk=chat_id)
            context['messages'] = Message.objects.filter(chat_id=chat_id).order_by('timestamp')
            context['form'] = MessageForm()
        else:
            context['selected_chat'] = None
            context['messages'] = None
            context['form'] = None
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = MessageForm(request.POST)
        if form.is_valid():
            chat_id = self.kwargs.get('pk')
            chat = Chat.objects.get(pk=chat_id)
            auth_person = get_object_or_404(Person, user=request.user)
            Message.objects.create(
                chat = chat,
                sender = auth_person,
                content = form.cleaned_data['message']
            )
            return redirect('abilityhub:chat', pk=chat.id)
        return render(request, self.template_name, self.get_context_data(form=form))

@login_required
def openchat(request, person_id):
    auth_person = get_object_or_404(Person, user=request.user)
    other_person = get_object_or_404(Person, pk=person_id)
    chat = Chat.objects.filter(participants=auth_person).filter(participants=other_person).first()
    if chat is None:
        with transaction.atomic():
            chat = Chat.objects.create()
            chat.participants.add(auth_person, other_person)

    return redirect('abilityhub:chat', pk=chat.id)

class TransactionsView(LoginRequiredMixin, generic.ListView):
    template_name = 'abilityhub/transactions.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        transactions = Transaction.objects.filter(
            Q(sender=self.request.user.person) | Q(receiver=self.request.user.person)
        ).annotate(type=Value('transaction', CharField())).order_by('-timestamp')
        deposits = Deposit.objects.filter(depositor = self.request.user.person).annotate(
            type=Value('deposit', CharField())).order_by('-timestamp')
        
        combined = sorted(
            chain(transactions, deposits),
            key=lambda x: x.timestamp,
            reverse=True
        )

        return combined

class DepositView(LoginRequiredMixin, generic.TemplateView):
    model = Person
    template_name = 'abilityhub/deposit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get("form", DepositForm())
        return context
    
    def post(self, request, *args, **kwargs):
        form = DepositForm(request.POST)
        if form.is_valid():
            depositor = request.user.person
            payment_method = form.cleaned_data['payment_method']
            added_credits = form.cleaned_data['added_credits']
            with transaction.atomic():
                depositor.credits += added_credits
                depositor.save()

                Deposit.objects.create(
                    depositor = depositor,
                    payment_method = payment_method,
                    added_credits = added_credits,
                    depositor_credits_after = depositor.credits,
                )
            request.session['added_credits'] = added_credits
            return redirect('abilityhub:depositsuccess')
        
        if form.errors:
            error_json = form.errors.as_json()
            error_dict = json.loads(error_json)
            
            for field, errors in error_dict.items():
                for error in errors:
                    error_message = error['message']
                    logger.warning(f'Form error in {field}: {error_message}', extra={
                        'interaction_id': request.interaction_id,
                        'application': APPLICATION_IDENTIFIER,
                        'code_location': self.__class__.__name__,
                        'user': request.user.username,
                        'event_type': 'validation_error',
                        'event_code': error['code'],
                        'description': f'Form error in {field}: {error_message}'
                })
        return render(request, self.template_name, self.get_context_data(form=form))

# Broken Access Control (fix commented)
class DescriptionView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'abilityhub/description.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auth_person = self.request.user.person
        context['form'] = DescriptionForm(initial={'description': auth_person.description})
        return context
    
    def post(self, request, *args, **kwargs):
        form = DescriptionForm(request.POST)
        if form.is_valid():
            auth_person = request.user.person
            auth_person.description = form.cleaned_data['description']
            auth_person.save()
            return redirect('abilityhub:myprofile', pk=auth_person.pk)
        return render(request, self.template_name, self.get_context_data(form=form))

# CSRF (replaces the safe version of SendView below)
@method_decorator(csrf_exempt, name="dispatch")
class SendView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'abilityhub/send.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person_id = self.request.session.get('person')
        context['person'] = Person.objects.get(id=person_id)
        return context
    
    def post(self, request, *args, **kwargs):
        auth_pk = request.POST.get('from')
        sender = get_object_or_404(Person, pk=auth_pk)
        sent_credits = request.POST.get('credits')
        receiver = get_object_or_404(Person, pk=kwargs['pk'])

        if int(auth_pk) != request.user.person.pk:
            messages.error(request, f'Something went wrong.')
            return render(request, self.template_name, self.get_context_data(person=receiver))

        if not sent_credits:
            messages.error(request, 'Please enter the number of credits you wish to send.')
            return render(request, self.template_name, self.get_context_data(person=receiver))
        
        try:
            sent_credits = int(sent_credits)
            if sent_credits <= 0:
                raise ValueError('Credits must be a positive number.')
        except ValueError:
            messages.error(request, 'Credits must be a positive number.')
            return render(request, self.template_name, self.get_context_data(person=receiver))

        with transaction.atomic():
            if sender == receiver:
                messages.error(request, 'You cannot send credits to yourself.')
                return render(request, self.template_name, self.get_context_data(person=receiver))
            
            if sender.credits >= sent_credits:
                sender.credits -= sent_credits
            else:
                messages.error(request, 'You do not have enough credits to complete this transaction.')
                return render(request, self.template_name, self.get_context_data(person=receiver))
            
            receiver.credits += sent_credits

            sender.save()
            receiver.save()

            Transaction.objects.create(
                sender = sender, 
                receiver = receiver,
                sender_credits_after = sender.credits,
                receiver_credits_after = receiver.credits,
                sent_credits = sent_credits,
            )
        request.session['receiver_id'] = receiver.id
        request.session['sent_credits'] = sent_credits
        return redirect('abilityhub:sendsuccess')

""" class SendView(LoginRequiredMixin, generic.DetailView):
    model = Person
    template_name = 'abilityhub/send.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get("form", SendForm())
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SendForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                sent_credits = form.cleaned_data['sent_credits']
                sender = get_object_or_404(Person, user=request.user)
                receiver = get_object_or_404(Person, pk=kwargs['pk'])

                if sender == receiver:
                    logger.warning(f'Form error: You cannot send credits to yourself.', extra={
                        'interaction_id': request.interaction_id,
                        'application': APPLICATION_IDENTIFIER,
                        'code_location': self.__class__.__name__,
                        'user': request.user.username,
                        'event_type': 'validation_error',
                        'event_code': 'invalid',
                        'description': 'User tried sending credits to themselves.'
                    })
                    messages.error(request, 'You cannot send credits to yourself.')
                    return render(request, self.template_name, self.get_context_data(form=form))
                
                if sender.credits >= sent_credits:
                    sender.credits -= sent_credits
                else:
                    logger.warning(f'Form error in sent_credits: You do not have enough credits to complete this transaction.', extra={
                        'interaction_id': request.interaction_id,
                        'application': APPLICATION_IDENTIFIER,
                        'code_location': self.__class__.__name__,
                        'user': request.user.username,
                        'event_type': 'validation_error',
                        'event_code': 'invalid',
                        'description': f'User with {sender.credits} credits tried sending {sent_credits} credits.'
                    })
                    messages.error(request, 'You do not have enough credits to complete this transaction.')
                    return render(request, self.template_name, self.get_context_data(form=form))
                
                receiver.credits += sent_credits

                sender.save()
                receiver.save()

                Transaction.objects.create(
                    sender = sender, 
                    receiver = receiver,
                    sender_credits_after = sender.credits,
                    receiver_credits_after = receiver.credits,
                    sent_credits = sent_credits,
                )
            request.session['receiver_id'] = receiver.id
            request.session['sent_credits'] = sent_credits
            return redirect('abilityhub:sendsuccess')
        
        if form.errors:
            error_json = form.errors.as_json()
            error_dict = json.loads(error_json)
            
            for field, errors in error_dict.items():
                for error in errors:
                    error_message = error['message']
                    logger.warning(f'Form error in {field}: {error_message}', extra={
                        'interaction_id': request.interaction_id,
                        'application': APPLICATION_IDENTIFIER,
                        'code_location': self.__class__.__name__,
                        'user': request.user.username,
                        'event_type': 'validation_error',
                        'event_code': error['code'],
                        'description': f'Form error in {field}: {error_message}'
                })
                    
        return render(request, self.template_name, self.get_context_data(form=form)) """

class SendSuccessView(LoginRequiredMixin, generic.DetailView):
    model = Person
    template_name = 'abilityhub/sendsuccess.html'
    context_object_name = 'receiver'

    def get_object(self):
        receiver_id = self.request.session.get('receiver_id')
        if receiver_id:
            return Person.objects.get(id=receiver_id)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sent_credits'] = self.request.session.get('sent_credits')
        return context
    
class DepositSuccessView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'abilityhub/depositsuccess.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['added_credits'] = self.request.session.get('added_credits')
        return context