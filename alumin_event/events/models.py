from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.forms import CharField
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField




class Event(models.Model):
    EVENT_TYPES = [
        ('networking', 'Networking'),
        ('round_table', 'Round Table'),
        ('startup_discussion', 'Startup Discussion'),
        ('campus_tour', 'Campus Tour / Meetup'),
        ('social', 'Social'),
        ('family_friends', 'Family / Friends Event'),
    ]

    LOCATION_TYPES = [
        ('offline', 'Offline'),
        ('online', 'Online'),
    ]

    name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    date = models.DateTimeField(null=True, blank=True)
    event_end_date = models.DateTimeField(null=True, blank=True)
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPES)
    physical_address = models.CharField(max_length=200, blank=True, null=True)
    online_link = models.URLField(blank=True, null=True)
    host = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    about = RichTextField(null=True)

    

    def __str__(self):
        return self.name

    def clean(self):
        """
        Ensure that either physical_address or online_link is provided based on location_type.
        """
        from django.core.exceptions import ValidationError
        if self.location_type == 'offline' and not self.physical_address:
            raise ValidationError("Offline events must have a physical address.")
        if self.location_type == 'online' and not self.online_link:
            raise ValidationError("Online events must have a link.")


class AgendaItem(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='agenda_items')
    title = models.CharField(max_length=200)  # e.g., "Welcome Speech"
    description = RichTextField(blank=True, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True,blank=True)
    speaker = models.CharField(max_length=100, blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.start_time} - {self.end_time})"



class Beverage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='beverages')
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)  # optional, track stock
    notes = RichTextField(blank=True, null=True)  # optional

    def __str__(self):
        return f"{self.name} ({self.event.name})"
    
    
    
    



FIELD_TYPES = [
    ("text", "Text"),
    ("number", "Number"),
    ("email", "Email"),
    ("textarea", "Textarea"),
    ("date", "Date"),
    ("file", "File"),
    ("dropdown", "Dropdown"),
]

class FormDefinition(models.Model):
    name = models.CharField(max_length=255)
    event_name = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='form_definitions',null =True, blank=True)
    description = RichTextField(blank=True)
   
    # Payment settings
    requires_payment = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_submissions_per_user = models.PositiveIntegerField(default=1)
    

    def __str__(self):
        return self.name


class DynamicField(models.Model):
    form = models.ForeignKey(FormDefinition, related_name="fields", on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    required = models.BooleanField(default=True)
    choices = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.label} ({self.form.name})"


class FormSubmission(models.Model):
    form = models.ForeignKey(FormDefinition, related_name="submissions", on_delete=models.CASCADE)
    data = models.JSONField()
    submitted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.form.name} at {self.created_at}"
    
class SubmissionFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    submission = models.ForeignKey(
        FormSubmission, related_name="files", on_delete=models.CASCADE
    )
    field = models.ForeignKey(DynamicField, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")  # stored under MEDIA_ROOT

    def __str__(self):
        return f"File for {self.field.label} (submission #{self.submission_id})"


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"
    
    
    


    
    
    
class Order(models.Model):
    user_name = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    amount = models.FloatField("Amount", null=False, blank=False)
    status = models.CharField(
        "Payment Status",
        default="pending",
        max_length=254,
        blank=False,
        null=False,
    )
    provider_order_id = models.CharField(
        "Order ID", max_length=40, null=False, blank=False
    )
    payment_id = models.CharField(
        "Payment ID", max_length=36, null=False, blank=False
    )
    signature_id = models.CharField(
        "Signature ID", max_length=128, null=False, blank=False
    )

    def __str__(self):
        return f"{self.user_name} - {self.status}"
    
    
    
    
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_registered_event = models.ForeignKey(FormSubmission, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[("intiated","Intiated"),("pending", "Pending"),("success","Success"), ("failed", "Failed")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user.username} - {self.status}"
    
 
    
    
    


class Student(models.Model):
    STATUS_CHOICES = [
        ("private", "Working in private organization"),
        ("business", "Business/Entrepreneur"),
        ("education", "Pursuing Higher Education"),
        ("others", "Others"),
    ]
    
    # Basic student info
    university_register_number = models.CharField(max_length=50,  null=False, blank=False, default="UNKNOWN")
    roll_no = models.CharField(max_length=50,  null=False, blank=False, default="UNKNOWN")
    f_name = models.CharField(max_length=100, null=False, blank=False, default="N/A")  # First name
    lname = models.CharField(max_length=100, null=False, blank=False, default="N/A")   # Last name
    student_name = models.CharField(max_length=200, null=False, blank=False, default="N/A")  # full name if needed
    gender = models.CharField(
        max_length=10,
        choices=[('Male','Male'),('Female','Female'),('Other','Other')],
        null=False,
        blank=False,
        default='Other'
    )
    date_of_birth = models.DateField(null=False, blank=False, default="2000-01-01")
    mobile_number = models.CharField(max_length=15, null=False, blank=False, default="0000000000")
    state = models.CharField(max_length=50, null=False, blank=False, default="N/A")
    email_id = models.EmailField(null=False, blank=False, default="example@example.com")
    
    # Father info
    father_name = models.CharField(max_length=200, null=False, blank=False, default="N/A")
    father_mobile_number = models.CharField(max_length=15, null=False, blank=False, default="0000000000")
    father_occupation = models.CharField(max_length=100, null=False, blank=False, default="N/A")
    father_organization = models.CharField(max_length=200, null=False, blank=False, default="N/A")
    
    # Mother info
    mother_name = models.CharField(max_length=200, null=False, blank=False, default="N/A")
    mother_mobile_number = models.CharField(max_length=15, null=False, blank=False, default="0000000000")
    mother_occupation = models.CharField(max_length=100, null=False, blank=False, default="N/A")
    mother_organization = models.CharField(max_length=200, null=False, blank=False, default="N/A")
    
    # Education / Placement
    batch = models.CharField(max_length=20, null=False, blank=False, default="N/A")
    department = models.CharField(max_length=100, null=False, blank=False, default="N/A")
    current_location = models.CharField(max_length=200, null=True, blank=True, default="N/A")
    current_company = models.CharField(max_length=200, null=False, blank=False, default="N/A")
    designation = models.CharField(max_length=100, null=True, blank=True, default="N/A")
    position = models.CharField(max_length=100, null=False, blank=False, default="N/A")  # if different from designation
    job_domain = models.CharField(max_length=100, null=False, blank=False, default="N/A")
    current_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="other"
    )

    # --- Private Organization ---
    organization = models.CharField(max_length=200, blank=True, null=True)
    # designation = models.CharField(max_length=100, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)

    # --- Business ---
    business_type = models.CharField(max_length=50, blank=True, null=True)
    company_type = models.CharField(max_length=50, blank=True, null=True)
    business_org_name = models.CharField(max_length=200, blank=True, null=True)
    business_designation = models.CharField(max_length=100, blank=True, null=True)
    business_location = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # --- Higher Education ---
    degree_program = models.CharField(max_length=200, blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    education_location = models.CharField(max_length=200, blank=True, null=True)

    # --- Others ---
    other_status_details = models.TextField(blank=True, null=True)
    
    # Contact info
    phone_number = models.CharField(max_length=15, null=False, blank=False, default="0000000000")
    phone_number2 = models.CharField(max_length=15, null=False, blank=False, default="1000000000")
    personal_email_id = models.EmailField(null=False, blank=False, default="example@example.com")
    official_email_id = models.EmailField(null=False, blank=False, default="example@example.com")
    linkedin_link = models.URLField(null=False, blank=False, default="http://example.com")
    
    def __str__(self):
        return f"{self.f_name} {self.lname} ({self.roll_no})"
