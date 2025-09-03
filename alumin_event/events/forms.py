from django import forms
from .models import *
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms.widgets import ClearableFileInput
class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)

        # This loop adds the 'form-control' class and placeholders to every field
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            # Add a placeholder that matches the field's label
            if field.label:
                field.widget.attrs['placeholder'] = field.label
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field.label:
                field.widget.attrs['placeholder'] = field.label

class EventForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    event_end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    registration_deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = Event
        fields = [
            'name',
            'event_type',
            'date',
            'event_end_date',
            'location_type',
            'physical_address',
            'online_link',
            'host',
            "registration_deadline"
        ]

    def clean_date(self):
        event_date = self.cleaned_data.get("date")
        if event_date and event_date < timezone.now():
            raise forms.ValidationError("Event date cannot be in the past.")
        return event_date

    def clean_registration_deadline(self):
        deadline = self.cleaned_data.get("registration_deadline")
        if deadline and deadline < timezone.now():
            raise forms.ValidationError("Registration deadline cannot be in the past.")
        return deadline
    def clean_event_end_date(self):
        event_end_date = self.cleaned_data.get("event_end_date")
        if event_end_date and event_end_date < timezone.now():
            raise forms.ValidationError("Event end date cannot be in the past.")
        return event_end_date

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get("date")
        event_end_date = cleaned_data.get("event_end_date")
        deadline = cleaned_data.get("registration_deadline")

        if event_end_date and event_end_date < event_date:
            raise forms.ValidationError("Event end date must be after event start date.")

        return cleaned_data

from django import forms

class AgendaItemForm(forms.ModelForm):
    start_time= forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    class Meta:
        model = AgendaItem
        fields = ['title', 'description', 'start_time', 'end_time', 'speaker', 'order']
        

    def __init__(self, *args, **kwargs):
        # Expect the event instance to be passed when creating the form
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if self.event:
            event_start = self.event.date  # or self.event.date if it's a datetime field
            event_end = self.event.event_end_date      # make sure you have event.end_time

            if start and start < event_start:
                print("error 1")
                raise forms.ValidationError("Agenda start time cannot be before the event starts.")

            if end and end > event_end:
                print("error 2")
                raise forms.ValidationError("Agenda end time cannot be after the event ends.")

        if start and end and end <= start:
            print("error 3 ")
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data

        
class BeverageForm(forms.ModelForm):
    class Meta:
        model = Beverage
        fields = ['name', 'quantity', 'notes']






class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = ["name",  "event_name", "description", "requires_payment", "payment_amount"]


class DynamicFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicField
        fields = ["label", "field_type", "required","choices"]
        widgets = {
            "choices": forms.Textarea(
                attrs={"placeholder": "Enter options separated by commas, e.g. User-Rs.0,Royal-Rs.2000"}
            )
        }


    def generate_dynamic_form_list(form_definition):
   
     fields={}

     for field in form_definition.fields.all():
        field_key = f"field_{field.id}" 
        if field.field_type == "text":
            form_field = forms.CharField(label=field.label, required=field.required)
        elif field.field_type == "number":
            form_field = forms.IntegerField(label=field.label, required=field.required)
        elif field.field_type == "email":
            form_field = forms.EmailField(label=field.label, required=field.required)
        elif field.field_type == "textarea":
            form_field = forms.CharField(label=field.label, widget=forms.Textarea, required=field.required)
        elif field.field_type == "date":
            form_field = forms.DateField(label=field.label, widget=forms.DateInput(attrs={"type": "date"}), required=field.required)
        elif field.field_type == "file":
            form_field = forms.FileField(
                label=field.label,
                required=field.required,
                widget=ClearableFileInput(attrs={
                    # adjust “accept” if you want to restrict types, e.g. "application/pdf,image/*"
                    "accept": "*/*"
                })
                # validators=[FileExtensionValidator(['pdf','png','jpg'])]  # optional
            )
        elif field.field_type.lower() == "dropdown":
            # Dropdown choices must be defined in field.choices (comma-separated)
            # Example: "USER:1. User – Rs.0,ROYAL:2. Royal – Rs.2000"
            choice_list = []
            if hasattr(field, 'choices') and field.choices:
                for c in field.choices.split(","):
                    if ":" in c:
                        val, display = c.split(":", 1)
                        choice_list.append((val.strip(), display.strip()))
                    else:
                        choice_list.append((c.strip(), c.strip()))
                    fields[field_key] = forms.ChoiceField(
                label=field.label,
                choices=choice_list,
                required=field.required
            )
        else:
            form_field = forms.CharField(label=field.label, required=field.required)

        DynamicFieldForm.base_fields[field.label] = form_field

     return DynamicFieldForm



from django import forms
from django.forms.widgets import ClearableFileInput

def generate_dynamic_form(form_definition):
    """
    Build a Django Form dynamically from FormDefinition + DynamicField,
    including dropdowns with user-friendly names.
    """
    fields = {}  # dictionary of field_name → form_field

    for field in form_definition.fields.all():
        field_key = f"field_{field.id}"  # unique field name

        if field.field_type.lower() == "text":
            fields[field_key] = forms.CharField(label=field.label, required=field.required)
        elif field.field_type.lower() == "number":
            fields[field_key] = forms.IntegerField(label=field.label, required=field.required)
        elif field.field_type.lower() == "email":
            fields[field_key] = forms.EmailField(label=field.label, required=field.required)
        elif field.field_type.lower() == "textarea":
            fields[field_key] = forms.CharField(label=field.label, widget=forms.Textarea, required=field.required)
        elif field.field_type.lower() == "date":
            fields[field_key] = forms.DateField(label=field.label, widget=forms.DateInput(attrs={"type": "date"}), required=field.required)
        elif field.field_type.lower() == "file":
            fields[field_key] = forms.FileField(
                label=field.label,
                required=field.required,
                widget=ClearableFileInput(attrs={"accept": "*/*"})
            )
        elif field.field_type.lower() == "dropdown":
            # Dropdown choices must be defined in field.choices (comma-separated)
            # Example: "USER:1. User – Rs.0,ROYAL:2. Royal – Rs.2000"
            choice_list = []
            if hasattr(field, 'choices') and field.choices:
                for c in field.choices.split(","):
                    if ":" in c:
                        val, display = c.split(":", 1)
                        choice_list.append((val.strip(), display.strip()))
                    else:
                        choice_list.append((c.strip(), c.strip()))
            fields[field_key] = forms.ChoiceField(
                label=field.label,
                choices=choice_list,
                required=field.required
            )
        else:
            fields[field_key] = forms.CharField(label=field.label, required=field.required)

    # Dynamically create a new Form class
    DynamicSubmissionForm = type('DynamicSubmissionForm', (forms.Form,), fields)
    return DynamicSubmissionForm




class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['f_name','lname','personal_email_id', 'position']
        
        
        
        
# forms.py

class StudentUploadForm(forms.Form):
    file = forms.FileField(label="Upload Excel File")




class CustomSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        
        
        
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'