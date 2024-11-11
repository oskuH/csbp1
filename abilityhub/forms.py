from django import forms

class UserRegistrationForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150)
    first_name = forms.CharField(label="First name", max_length=150)
    last_name = forms.CharField(label="Last name", max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username.lower() == "deleted":
            # 'deleted' is reserved for deleted users whose Person still exists
            # note: functionality to delete users is not currently
            raise forms.ValidationError("Prohibited username.")
        
        return username

class ImageForm(forms.Form):
    title = forms.CharField(label="Image title", max_length=50)
    image = forms.ImageField()

class MessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

DEPOSIT_CHOICES = (
    ("credit_card", "Credit Card"),
    ("bank_account", "Bank account"),
    ("mobilepay", "MobilePay")
)

class DepositForm(forms.Form):
    added_credits = forms.IntegerField(
        label="How many credits would you like to add?", 
        min_value=1,
        error_messages={
            'required': "Credit amount must be a positive whole number.",
            'invalid': "Credit amount must be a positive whole number.",
            'min_value': "You must deposit at least 1 credit.",
        })
    payment_method = forms.ChoiceField(label="Payment method", choices=DEPOSIT_CHOICES)
    
class DescriptionForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea, label="Description")

class SendForm(forms.Form):
    sent_credits = forms.IntegerField(
        label="Credits", 
        min_value=1,
        error_messages={
            'required': "Credit amount must be a positive whole number.",
            'invalid': "Credit amount must be a positive whole number.",
            'min_value': "You must send at least 1 credit."
        })