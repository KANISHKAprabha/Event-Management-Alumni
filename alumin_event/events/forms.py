from django import forms
from .models import *
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms.widgets import ClearableFileInput
from ckeditor.widgets import CKEditorWidget

class CustomSignupForm(UserCreationForm):
    """
    A custom user creation form that includes first name, last name, and email,
    and applies Bootstrap styling to all fields.
    """
    # Define the additional fields you want on your sign-up form.
    # The parent UserCreationForm already handles username and passwords.
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    email = forms.EmailField(max_length=254, required=True, label='Email address')

    class Meta(UserCreationForm.Meta):
        model = User
        # Specify all the fields to be displayed on the form.
        # The password fields are handled by the form's logic, not by Meta.
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        """
        This is where we apply the styling.
        This method runs when the form is created.
        """
        # First, run the original __init__ method from the parent class.
        super().__init__(*args, **kwargs)
        
        # Now, loop over all the fields that the form has...
        for field_name, field in self.fields.items():
            # ...and add the 'form-control' class to each one's widget.
            # This is what makes them look like the Bootstrap-styled email field.
            field.widget.attrs['class'] = 'form-control'
            
            # Optional but recommended: Add a placeholder based on the field's label.
            if field.label and not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        """
        Override the save method to save the extra data (first_name, last_name, email).
        """
        # First, run the parent's save method to create the user object.
        user = super().save(commit=False)
        
        # Then, add your custom data from the form's cleaned_data dictionary.
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        
        # Finally, save the user to the database if commit is True.
        if commit:
            user.save()
            
        return user

class EventForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    event_end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    registration_deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
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
            "registration_deadline",
            "image",
            "about"
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'location_type': forms.Select(attrs={'class': 'form-select'}),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'online_link': forms.URLInput(attrs={'class': 'form-control'}),
            'host': forms.TextInput(attrs={'class': 'form-control'}),
            'about': forms.TextInput(attrs={'class': 'form-control', 'style': "width: 100%;"}),
        }

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



class AgendaItemForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    class Meta:
        model = AgendaItem
        fields = ['title', 'description', 'start_time', 'end_time', 'speaker', 'order']

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

        # Add Bootstrap form-control class to all fields except hidden inputs
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.HiddenInput):
                # Make description textarea fixed height
                if field_name == 'description':
                    field.widget.attrs.update({'class': 'form-control', 'style': 'height:120px;'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if self.event:
            event_start = self.event.date
            event_end = self.event.event_end_date

            if start and start < event_start:
                raise forms.ValidationError("Agenda start time cannot be before the event starts.")
            if end and end > event_end:
                raise forms.ValidationError("Agenda end time cannot be after the event ends.")

        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


        
class BeverageForm(forms.ModelForm):
    class Meta:
        model = Beverage
        fields = ['name', 'quantity', 'notes']






class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = [
            "name", "event_name", "description", 
            "requires_payment", "payment_amount",  
            "max_submissions_per_user"
        ]
        widgets = {
            "description": CKEditorWidget(attrs={"style": "width: 100%;"}),  # 👈 force full width
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != "description":  # CKEditor already styled
                if not isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs.update({'class': 'form-control'})



class DynamicFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicField
        fields = ["label", "field_type", "required", "choices"]
        widgets = {
            "choices": forms.Textarea(
                attrs={
                    "placeholder": "Enter options separated by commas, e.g. User-Rs.0,Royal-Rs.2000",
                    "class": "form-control"  # add form-control here
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                if "class" in field.widget.attrs:
                    field.widget.attrs["class"] += " form-control"
                else:
                    field.widget.attrs["class"] = "form-control"



    def generate_dynamic_form_list(form_definition):
   
     fields={}

     for field in form_definition.fields.all():
        field_key = f"field_{field.id}" 
        if field.field_type == "text":
            form_field = forms.CharField(label=field.label, required=field.required,widget=forms.TextInput(attrs={"class": "form-control"}))
        elif field.field_type == "number":
            form_field = forms.IntegerField(label=field.label, required=field.required,widget=forms.NumberInput(attrs={"class": "form-control"}))
        elif field.field_type == "email":
            form_field = forms.EmailField(label=field.label, required=field.required,widget=forms.EmailInput(attrs={"class": "form-control"}))
        elif field.field_type == "textarea":
            form_field = forms.CharField(label=field.label, widget=forms.Textarea(attrs={"class": "form-control"}), required=field.required)
        elif field.field_type == "date":
            form_field = forms.DateField(label=field.label, widget=forms.DateInput(attrs={"type": "date","class": "form-control"}), required=field.required)
        elif field.field_type == "file":
            form_field = forms.FileField(
                label=field.label,
                required=field.required,
                widget=ClearableFileInput(attrs={
                    # adjust “accept” if you want to restrict types, e.g. "application/pdf,image/*"
                    "accept": "*/*",
                    "class": "form-control"
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
                required=field.required,
                 widget=forms.Select(attrs={"class": "form-select"})
                
            )
        else:
            form_field = forms.CharField(label=field.label, required=field.required)

        DynamicFieldForm.base_fields[field.label] = form_field

     return DynamicFieldForm



def generate_dynamic_form(form_definition):
    """
    Build a Django Form dynamically from FormDefinition + DynamicField,
    with Bootstrap-friendly widgets.
    """
    fields = {}

    for field in form_definition.fields.all():
        field_key = f"field_{field.id}"  # safe unique name

        if field.field_type.lower() == "text":
            fields[field_key] = forms.CharField(
                label=field.label,
                required=field.required,
                widget=forms.TextInput(attrs={"class": "form-control"})
            )
        elif field.field_type.lower() == "number":
            fields[field_key] = forms.IntegerField(
                label=field.label,
                required=field.required,
                widget=forms.NumberInput(attrs={"class": "form-control"})
            )
        elif field.field_type.lower() == "email":
            fields[field_key] = forms.EmailField(
                label=field.label,
                required=field.required,
                widget=forms.EmailInput(attrs={"class": "form-control"})
            )
        elif field.field_type.lower() == "textarea":
            fields[field_key] = forms.CharField(
                label=field.label,
                required=field.required,
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
            )
        elif field.field_type.lower() == "date":
            fields[field_key] = forms.DateField(
                label=field.label,
                required=field.required,
                widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
            )
        elif field.field_type.lower() == "file":
            fields[field_key] = forms.FileField(
                label=field.label,
                required=field.required,
                widget=ClearableFileInput(attrs={
                    "accept": "*/*",
                    "class": "form-control"
                })
            )
        elif field.field_type.lower() == "dropdown":
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
                required=field.required,
                widget=forms.Select(attrs={"class": "form-select"})
            )
        else:
            fields[field_key] = forms.CharField(
                label=field.label,
                required=field.required,
                widget=forms.TextInput(attrs={"class": "form-control"})
            )

    # Dynamically create form class
    DynamicSubmissionForm = type('DynamicSubmissionForm', (forms.Form,), fields)
    return DynamicSubmissionForm


class StudentRegistrationForm(forms.ModelForm):
    joining_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month", "class": "form-control"})
    )
    class Meta:
        model = Student
        fields = [
            "f_name",
            "lname",
            "personal_email_id",
            "current_status",
            "organization",
            "designation",
            "joining_date",
            "business_org_name",
            "business_designation",
            "business_type",
            "company_type",
            "business_location",
            "website",
            "degree_program",
            "institution",
            "education_location",
            "other_status_details",
        ]
        widgets = {
            "f_name": forms.TextInput(attrs={"class": "form-control"}),
            "lname": forms.TextInput(attrs={"class": "form-control"}),
            "personal_email_id": forms.EmailInput(attrs={"class": "form-control"}),
            "current_status": forms.Select(attrs={"class": "form-control", "id": "current_status"}),
            "organization": forms.TextInput(attrs={"class": "form-control"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
           
            "business_org_name": forms.TextInput(attrs={"class": "form-control"}),
            "business_designation": forms.TextInput(attrs={"class": "form-control"}),
            "business_location": forms.TextInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "degree_program": forms.TextInput(attrs={"class": "form-control"}),
            "institution": forms.TextInput(attrs={"class": "form-control"}),
            "education_location": forms.TextInput(attrs={"class": "form-control"}),
            "other_status_details": forms.Textarea(attrs={"class": "form-control"}),
        }


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