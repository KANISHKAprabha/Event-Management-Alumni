from datetime import datetime
from urllib.parse import urlencode
import json
from django.forms import modelformset_factory
from django.db.models import Count
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db import transaction
from .tasks import *
from django.urls import reverse_lazy, reverse
from django.db.models import Prefetch
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q 
from django.urls import reverse_lazy
from .decorators import event_login_required
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from .permissions import is_admin, is_user
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import user_passes_test
import warnings
import razorpay
from django.conf import settings
import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import StudentUploadForm
from .tasks import import_students_from_excel

warnings.filterwarnings("ignore", category=UserWarning, module="razorpay")

def signup_view(request):
  try:
    messages.info(request, "Please Register for event  to continue")
    return redirect('event_overview')
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            try:
                group, _ = Group.objects.get_or_create(name='User')
                user.groups.add(group)
            except Exception as group_err:
                logger.warning("Unable to add user to 'User' group: %s", group_err, exc_info=True)
            login(request, user)
            return redirect('login')  # redirect to events page
    else:
        form = CustomSignupForm()
    return render(request, 'accounts/signup.html', {'form': form})
  except Exception as e:
    print(e,"line no 53")
    messages.error(request, "An error occurred during signup. Please try again.")
    return render(request, 'errors/error.html',)


# Login view
def login_view(request):
 try:
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            login(request, user)
            
            if user.groups.filter(name='Admin').exists():
                return redirect('event_list')
             # redirect after login
            return redirect('event_overview')
        else:
            messages.info(request, " Log is not successful .Please Register for event  to continue")
    else:
        messages.info(request, "Please Register for event  to continue")
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})
 except Exception as e:
     print(e,"error")
     logger.error(f"Error in login_view: {e}", exc_info=True)
     messages.error(request, "An error occurred during login. Please try again.")
     return render(request, 'errors/error.html',)

def user_login(request,event_id):
 try:
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            login(request, user)
            
            if user.groups.filter(name='Admin').exists():
                return redirect('event_list')
             # redirect after login
            return redirect('register_event', event_id=event_id)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})
 except Exception as e:
     print(e,"error")
     logger.error(f"Error in login_view: {e}", exc_info=True)
     messages.error(request, "An error occurred during login. Please try again.")
     return render(request, 'errors/error.html',)

# Logout view
def logout_view(request):
    logout(request)
    return redirect('event_overview')

# ---------- Event Views ----------
@login_required
@user_passes_test(is_admin)
def event_list(request):
 try:
    ordered_agendas_queryset = AgendaItem.objects.order_by('order')
    events = Event.objects.all().prefetch_related(
            Prefetch('agenda_items', queryset=ordered_agendas_queryset),
            'beverages',
             
        )
    # print(events.agenda_items.all(),"line no 119")
    # print(events.beverages.all(),"line no 120")
    
    dynamic_forms = FormDefinition.objects.all()
    sub = FormSubmission.objects.all()
    
    context = {
        'events': events,
        'dynamic_forms': dynamic_forms,
        'submissions': sub, 
        'now': timezone.now(),  # for registration deadline check
    }
    return render(request, 'events/event_list.html', context)
 except Exception as e:
     print(e,"line no 134")
     logger.error(f"Error in event_list: {e}", exc_info=True)
     messages.error(request, "An error occurred while loading events. Please try again.")
     return render(request, 'errors/error.html',)
@event_login_required
def event_detail(request, pk):
 try:
    event = get_object_or_404(Event, pk=pk)
    agenda_items = event.agenda_items.all()
    return render(request, 'events/event_detail.html', {'event': event, 'agenda_items': agenda_items})
 except Exception as e:
     logger.error(f"Error in event_detail: {e}", exc_info=True)
     messages.error(request, "An error occurred while loading event details. Please try again.")
     return render(request, 'errors/error.html',)
@login_required
@user_passes_test(is_admin)
def event_create(request):
 try:
    if request.method == 'POST':
        form = EventForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Event created successfully!")
            return redirect('event_list')
        else:
            print(form.errors.as_json())
            
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})
 except Exception as e:
     logger.error(f"Error in event_create: {e}", exc_info=True)
     messages.error(request, "An error occurred while creating the event. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def event_update(request, pk):
 try:
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Event updated successfully!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form})
 except Exception as e:
     logger.error(f"Error in event_update: {e}", exc_info=True)
     messages.error(request, "An error occurred while updating the event. Please try again.")
     return render(request, 'errors/error.html',)
@login_required
@user_passes_test(is_admin)
def event_delete(request, pk):
 try:
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('event_list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})
 except Exception as e:
     logger.error(f"Error in event_delete: {e}", exc_info=True)
     messages.error(request, "An error occurred while deleting the event. Please try again.")
     return render(request, 'errors/error.html',)



# ---------- AgendaItem Views ----------
@login_required
@user_passes_test(is_admin)
def agenda_create(request, event_pk):
 try:
    event = get_object_or_404(Event, pk=event_pk)
     
    if request.method == 'POST':
        form = AgendaItemForm(request.POST,event=event)
        print("form in 55",request.POST)
        print(form.is_valid())
        if form.is_valid():
            agenda_item = form.save(commit=False)
            agenda_item.event = event
            agenda_item.save()
            messages.success(request, "✅ Agenda created successfully!")
            
            print("form in 60",request.POST)
            print("Saved agenda item:", agenda_item.pk, agenda_item.title, agenda_item.event)
            return redirect('event_detail',pk=event.pk)
    else:
        form = AgendaItemForm()
    return render(request, 'events/agenda_form.html', {'form': form, 'event': event})
 except Exception as e:
     logger.error(f"Error in agenda_create: {e}", exc_info=True)
     messages.error(request, "An error occurred while creating the agenda item. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def agenda_update(request, pk):
 try:
    agenda_item = get_object_or_404(AgendaItem, pk=pk)
    if request.method == 'POST':
        form = AgendaItemForm(request.POST, instance=agenda_item)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Agenda updated  successfully!")
            return redirect('event_detail', pk=agenda_item.event.pk)
    else:
        form = AgendaItemForm(instance=agenda_item)
    return render(request, 'events/agenda_form.html', {'form': form, 'event': agenda_item.event})
 except Exception as e:
     logger.error(f"Error in agenda_update: {e}", exc_info=True)
     messages.error(request, "An error occurred while updating the agenda item. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def agenda_delete(request, pk):
 try:
    agenda_item = get_object_or_404(AgendaItem, pk=pk)
    event_pk = agenda_item.event.pk
    if request.method == 'POST':
        agenda_item.delete()
        return redirect('event_detail', pk=event_pk)
    return render(request, 'events/agenda_confirm_delete.html', {'agenda_item': agenda_item})
 except Exception as e:
     logger.error(f"Error in agenda_delete: {e}", exc_info=True)
     messages.error(request, "An error occurred while deleting the agenda item. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def beverage_create(request, event_pk):
 try:
    event = get_object_or_404(Event, pk=event_pk)
    if request.method == 'POST':
        form = BeverageForm(request.POST)
        if form.is_valid():
            beverage = form.save(commit=False)
            beverage.event = event
            beverage.save()
            messages.success(request, "✅ Beverage added successfully!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = BeverageForm()
    return render(request, 'events/beverage_form.html', {'form': form, 'event': event})
 except Exception as e:
     logger.error(f"Error in beverage_create: {e}", exc_info=True)
     messages.error(request, "An error occurred while creating the beverage. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def beverage_update(request, pk):
 try:
    beverage = get_object_or_404(Beverage, pk=pk)
    if request.method == 'POST':
        form = BeverageForm(request.POST, instance=beverage)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Beverage updated successfully!")
            return redirect('event_detail', pk=beverage.event.pk)
    else:
        form = BeverageForm(instance=beverage)
    return render(request, 'events/beverage_form.html', {'form': form, 'event': beverage.event})
 except Exception as e:
     logger.error(f"Error in beverage_update: {e}", exc_info=True)
     messages.error(request, "An error occurred while updating the beverage. Please try again.")
     return render(request, 'errors/error.html',)

@user_passes_test(is_admin)
def beverage_delete(request, pk):
 try:
    beverage = get_object_or_404(Beverage, pk=pk)
    event_pk = beverage.event.pk
    if request.method == 'POST':
        beverage.delete()
        return redirect('event_detail', pk=event_pk)
    return render(request, 'events/beverage_confirm_delete.html', {'beverage': beverage})
 except Exception as e:
     logger.error(f"Error in beverage_delete: {e}", exc_info=True)
     messages.error(request, "An error occurred while deleting the beverage. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def create_form(request):
 try:
    if request.method == "POST":
        form = FormDefinitionForm(request.POST)
        if form.is_valid():
            form_def = form.save()
            return redirect("add_field", form_id=form_def.id)
    else:
        form = FormDefinitionForm()
    return render(request, "forms/create_form.html", {"form": form})
 except Exception as e:
     logger.error(f"Error in create_form: {e}", exc_info=True)
     messages.error(request, "An error occurred while creating the form. Please try again.")
     return render(request, 'errors/error.html',)

# Create already exists (your create_form)
@login_required
@user_passes_test(is_admin)
def update_form(request, pk):
 try:
    form_def = get_object_or_404(FormDefinition, pk=pk)
    if request.method == "POST":
        form = FormDefinitionForm(request.POST, instance=form_def)
        if form.is_valid():
            form.save()
            return redirect("event_list")  # redirect to listing page
    else:
        form = FormDefinitionForm(instance=form_def)
    return render(request, "forms/update_form.html", {"form": form, "form_def": form_def})
 except Exception as e:
     logger.error(f"Error in update_form: {e}", exc_info=True)
     messages.error(request, "An error occurred while updating the form. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def delete_form(request, pk):
 try:
    form_def = get_object_or_404(FormDefinition, pk=pk)
    if request.method == "POST":
        form_def.delete()
        return redirect("event_list")
    return render(request, "forms/delete_form.html", {"form_def": form_def})
 except Exception as e:
     logger.error(f"Error in delete_form: {e}", exc_info=True)
     messages.error(request, "An error occurred while deleting the form. Please try again.")
     return render(request, 'errors/error.html',)




# --- Admin: Add fields to a Form ---
@login_required
@user_passes_test(is_admin)
def add_field(request, form_id):
 try:
    form_def = get_object_or_404(FormDefinition, id=form_id)
    if request.method == "POST":
        field_form = DynamicFieldForm(request.POST)
        if field_form.is_valid():
            field = field_form.save(commit=False)
            field.form = form_def
            field.save()
            return redirect("add_field", form_id=form_def.id)
    else:
        field_form = DynamicFieldForm()
    return render(request, "forms/add_field.html", {"form_def": form_def, "field_form": field_form})
 except Exception as e:
     logger.error(f"Error in add_field: {e}", exc_info=True)
     messages.error(request, "An error occurred while adding the field. Please try again.")
     return render(request, 'errors/error.html',)

# --- User: Fill the form ---
@login_required
def fill_form(request, form_id):
  try:
    print("entered_fill form")
    form_def = get_object_or_404(FormDefinition, id=form_id)
    event_id = form_def.event_name.id
    print(event_id,"line no 415")
    DynamicFormClass = generate_dynamic_form(form_def)
    existing_count = FormSubmission.objects.filter(
            form=form_def, submitted_by=request.user
        ).count()
    remaining_submissions = max(0, form_def.max_submissions_per_user - existing_count)
    print(remaining_submissions,"line noooooooooooooooooooooo")
    
    
    
 

    if request.method == "POST":
        form = DynamicFormClass(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                submission = FormSubmission.objects.create(
                    form=form_def,
                    data=form.data,
                    submitted_by=request.user
                )

                payment_amount = form_def.payment_amount or 0
                if payment_amount == 0:
                    for value in submission.data.values():
                        if isinstance(value, str) and "Rs." in value:
                            try:
                                payment_amount = int(value.split("Rs.")[-1].strip())
                            except ValueError:
                                pass

                for field_def in form_def.fields.all():
                    field_key = f"field_{field_def.id}"
                    value = form.cleaned_data.get(field_key)
                    if field_def.field_type.lower() == "file" and value:
                        SubmissionFile.objects.create(
                            user=request.user,
                            submission=submission,
                            field=field_def,
                            file=value
                        )

                submission.save()

                if form_def.requires_payment:
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    razorpay_order = client.order.create(
                        {"amount": int(payment_amount * 100), "currency": "INR", "payment_capture": "1"}
                    )

                    payment = Payment.objects.create(
                        user=request.user,
                        user_registered_event=submission,
                        amount=payment_amount,
                        status="pending"
                    )

                    order = Order.objects.create(
                        user_name=request.user,
                        amount=payment_amount,
                        provider_order_id=razorpay_order["id"],
                        status="PENDING"
                    )

                    callback_url = request.build_absolute_uri(reverse("razorpay_callback"))
                    return render(
                        request,
                        "events/callback.html",
                        {
                            "callback_url": callback_url,
                            "razorpay_key": settings.RAZORPAY_KEY_ID,
                            "amount": payment_amount,
                            "order": order
                        },
                    )

                messages.success(request, "✅ Submitted successfully!")
                return redirect("register_event" ,event_id)
        else:
            print("error")
            logger.debug("Form errors: %s", form.errors)
    else:
        form = DynamicFormClass()

    return render(
        request,
        "forms/fill_form.html",
        {"form_def": form_def, "form": form,"remaining_submissions": remaining_submissions,"event_id":event_id}
    )
  except Exception as e:
    print(e,"errorrrrrrrrrrrrrrrr")
    logger.error("Error in fill_form: %s", e, exc_info=True)
    messages.error(request, "An error occurred while filling the form. Please try again.")
    return render(request, 'errors/error.html')


@csrf_exempt
def callback(request):
    print(request.POST,"line 285")
    def verify_signature(response_data):
        print(response_data,"line 292")
        print(request.user)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            return client.utility.verify_payment_signature(response_data)
        except razorpay.errors.SignatureVerificationError:
            return False

    if "razorpay_signature" in request.POST:
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order = Order.objects.get(provider_order_id=provider_order_id)
        print(order.amount,"line 302")
        order.payment_id = payment_id
        order.signature_id = signature_id
        order.save()
        
        if verify_signature(request.POST):
            order.status = 'ACCEPT'
            order.save()
            context={
                'order':order,
                'payment_amount': order.amount
            }
            payment = Payment.objects.get(user=order.user_name, amount=order.amount, status="pending")
            payment.status = "success"
            payment.save()
            from events.tasks import send_payment_receipt_email
            send_payment_receipt_email.delay(payment.id, order.id)
            
            print("SUCCESS")
            return render(request, "events/success.html",context)
        else:
            order.status = 'REJECT'
            order.save()
            payment = Payment.objects.get(user=order.user_name, amount=order.amount, status="pending")
            payment.status = "failed"
            payment.save()
            
            print("FAILURE: Signature verification failed.")
            return render(request, "events/failed.html", context={'order':order})
    else:
        try:
            payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
            provider_order_id = json.loads(request.POST.get("error[metadata]")).get("order_id")
        except (TypeError, json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing error metadata: {e}")
            return render(request, "events/callback.html", context={"status": 'REJECT'})

        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.status = 'REJECT'
        order.save()
        payment = Payment.objects.get(user=order.user_name, amount=order.amount, status="pending")
        payment.status = "failed"
        payment.save()
        print("FAILURE: Error in payment process.")
        return render(request, "events/callback.html", context={"status": order.status})
    
    
    


# def payment_success(request, order_id):
#     # ✅ Get the order
#     order = get_object_or_404(Order, id=order_id)

#     # ✅ Find related pending payment
#     payment = Payment.objects.filter(user=order.user, amount=order.amount, status="pending").first()

#     if payment:
#         payment.status = "success"
#         payment.save()

#     # 👉 Render your existing success template
#     return render(request, "events/success.html", {
#         "order": order,
#         "payment": payment,
#     })


# # --- Admin: View submissions ---
# def form_submissions(request, form_id):
#     form_def = get_object_or_404(FormDefinition, id=form_id)
#     submissions = form_def.submissions.all()
#     return render(request, "forms/form_submissions.html", {"form_def": form_def, "submissions": submissions})




def event_overview(request):
    try:
        # 1. Start with a base queryset for all events, ordered as you like.
        events_queryset = Event.objects.all().order_by('-date')

        # 2. Get the search query from the URL. It's good practice to strip whitespace.
        search_query = request.GET.get('q', '').strip()
        
        # 3. If a search query exists, filter the *existing* queryset.
        if search_query:
            # This modifies the events_queryset to be a filtered list.
            # If there's no query, this block is skipped, and the queryset remains unfiltered.
            events_queryset = events_queryset.filter(name__icontains=search_query)

        # 4. Now, apply prefetching to the final queryset (which is either all events or the filtered ones).
        # This is more efficient as you're only prefetching for the events you'll actually display.
        ordered_agendas_queryset = AgendaItem.objects.order_by('order')
        final_events = events_queryset.prefetch_related(
            Prefetch('agenda_items', queryset=ordered_agendas_queryset),
            'beverages'
        )

        # 5. Build the context with the single, correct queryset.
        # It's also helpful to pass the search query back to the template.
        context = {
            'events': final_events,
            'now': timezone.now(),
            'search_query': search_query, # Useful for showing "Results for '...'" or pre-filling the search box
        }
        
        return render(request, "events/event_overview.html", context)

    except Exception as e:
        # Your error handling is good.
        logger.error(f"Error in event_overview: {e}", exc_info=True)
        messages.error(request, "An error occurred while loading the event overview. Please try again.")
        return render(request, 'errors/error.html')


def list_event_registertion(request):
    try:
        registrations = EventRegistration.objects.select_related("event", "user").all()
        return render(request, "events/event_registeration_list.html", {"registrations": registrations})
    except Exception as e:
        logger.error(f"Error in list_event_registertion: {e}", exc_info=True)
        messages.error(request, "An error occurred while loading the registrations. Please try again.")
        return render(request, 'errors/error.html',)





def register_event(request, event_id):
 try:
    event = get_object_or_404(Event, id=event_id)

    # --- Step 2: Handle all exit conditions first (Guard Clauses) ---

    # Exit if registration is closed
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        return render(request, 'events/registration_closed.html', {'event': event})

    # Exit if user is not logged in (redirect to login)
    if not request.user.is_authenticated:
        post_login_redirect_url = reverse('register_event', kwargs={'event_id': event.id})
        google_login_url = reverse('social:begin', args=['google-oauth2'])
        params = urlencode({'next': post_login_redirect_url})
        google_login_url_with_next = f'{google_login_url}?{params}'
        
        context = {
            "event": event,
            "google_login_url": google_login_url_with_next,
        }
        return render(request, "events/registered_user.html", context)

    # From here, the user is authenticated.
    user = request.user

    # Exit if user is ALREADY registered for this event
    if EventRegistration.objects.filter(event=event, user=user).exists():
        messages.info(request, "You are already registered for this event.")
        return render(request, "events/already_registered.html", {"event": event})

    # --- Step 3: Main Logic for Authenticated, Unregistered Users ---

    # Try to find the user's existing Student profile
    student = Student.objects.filter(personal_email_id=user.email).first()
    year_choices = list(range(datetime.now().year, 2000, -1))
    print(year_choices,"linr no 638")# e.g. 2025 → 2001
    forms_sub = event.form_definitions.all()
    user_submissions = FormSubmission.objects.filter(
            form__in=forms_sub,
            submitted_by=request.user
        ).values(
            'form_id' # Group by form
        ).annotate(
            submission_count=Count('id') # Count submissions for each form
        )

        # Create a dictionary for easy lookup: {form_id: count}
    submission_counts = {item['form_id']: item['submission_count'] for item in user_submissions}

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, instance=student)

        if form.is_valid():
            student_instance = form.save(commit=False)
            
            # --- DATA CLEANUP LOGIC ---
            new_status = student_instance.current_status
            
            if new_status != 'private':
                student_instance.organization = None
                student_instance.designation = None
                student_instance.joining_date = None
                student_instance.current_location = ""

            if new_status != 'business':
                student_instance.business_org_name = None
                student_instance.business_designation = None
                student_instance.business_type = None
                student_instance.company_type = None
                student_instance.business_location = None
                student_instance.website = None

            if new_status != 'education':
                student_instance.degree_program = None
                student_instance.institution = None
                student_instance.education_location = None

            if new_status != 'others':
                student_instance.other_status_details = ""

            student_instance.save()
            
            EventRegistration.objects.create(event=event, user=user)
            send_registration_email(user.id, event.id)
            
            messages.success(request, f"✅ You have successfully registered for {event.name}!")
            return render(request, "events/already_registered.html", {"event": event})
        
        else:
            logger.warning(f"Registration form errors for user {user.email}: {form.errors.as_json()}")
            messages.error(request, "⚠️ Please correct the errors in the form below.")
    
    else:  # This is a GET request
        if student:
            form = StudentRegistrationForm(instance=student)
        else:
            form = StudentRegistrationForm(initial={
                'f_name': user.first_name,
                'l_name': user.last_name,
                'personal_email_id': user.email,
            })

    context = {
        'event': event,
        'form': form,
        'student': student,
        'forms_sub':forms_sub
    }
    return render(request, "events/registered_user.html", context)
 except Exception as e:
     print("error:", str(e))
     print(e,"line 680")
     return render(request, "errors/error.html", {"error": str(e)})
@user_passes_test(is_user)
def already_registered_view(request):
    user = request.user
    # form_submission =
    
    # Pass any context if needed
    context = {}
    return render(request, 'events/already_registered.html', context)

@login_required
@user_passes_test(is_admin)
def event_list_view(request):
 try:
    events = Event.objects.all()
    
    return render(request, "events/events_admin_list.html", {"events": events})
 except Exception as e:
     logger.error(f"Error in event_list_view: {e}", exc_info=True)
     messages.error(request, "An error occurred while loading the event list. Please try again.")
     return render(request, 'errors/error.html',)

@login_required
@user_passes_test(is_admin)
def event_submissions_view(request, event_id):
    try:
        event = get_object_or_404(Event, id=event_id)
        registrations = EventRegistration.objects.filter(event=event).select_related("user")
        print(registrations,"line   1")

        user_data = []
        for reg in registrations:
            submissions = FormSubmission.objects.filter(
                form__event_name=event, submitted_by=reg.user
            ).prefetch_related("files", "files__field")
            print(submissions,"lineeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

            submission_details = []
            for sub in submissions:
                # Map field_xx -> DynamicField.label
                labeled_data = {}
                for key, value in sub.data.items():
                    if key.startswith("field_"):  
                        try:
                            field_id = key.split("_")[1]
                            field = DynamicField.objects.get(id=field_id, form=sub.form)
                            labeled_data[field.label] = value
                        except (IndexError, DynamicField.DoesNotExist):
                            labeled_data[key] = value
                    else:
                        labeled_data[key] = value

                submission_details.append({
                    "submitted_at": sub.created_at,
                    "data": labeled_data,   # now labels instead of field_45
                    "files": sub.files.all()
                })

            user_data.append({
                "user": reg.user,
                "submissions": submission_details
            })

        return render(request, "events/events_admin_submission_view.html", {
            "event": event,
            "user_data": user_data
        })
    except Exception as e:
        print(e, "error")
        logger.error(f"Error in event_submissions_view: {e}", exc_info=True)
        messages.error(request, "An error occurred while loading event submissions. Please try again.")
        return render(request, 'errors/error.html')


@login_required
@user_passes_test(is_admin)

def event_payments_view(request, event_id):
 try:
    event = get_object_or_404(Event, id=event_id)

    # Get all payments related to this event
    payments = Payment.objects.filter(
        user_registered_event__form__event_name=event
    ).select_related("user", "order")

    context = {
        "event": event,
        "payments": payments
    }
    return render(request, "accounts/event_payment_view.html", context)
 except Exception as e:
    logger.error(f"Error in event_payments_view: {e}", exc_info=True)
    messages.error(request, "An error occurred while loading event payments. Please try again.")
    return render(request, 'errors/error.html',)




def upload_students(request):
    if request.method == "POST":
        form = StudentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data["file"]

            # Save to MEDIA folder
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, excel_file.name)

            with open(file_path, "wb+") as f:
                for chunk in excel_file.chunks():
                    f.write(chunk)

            # Run Celery task
            import_students_from_excel.delay(file_path)

            return HttpResponse("✅ Import started! Check Celery worker logs.")
    else:
        form = StudentUploadForm()

    return render(request, "students/upload_student.html", {"form": form})





class StudentListView(ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        """
        Override the default queryset to filter based on a search query.
        """
        queryset = super().get_queryset().order_by('f_name', 'lname')
        query = self.request.GET.get('q') # Get the search query from the URL parameter 'q'

        if query:
            # Filter the queryset to find students where the first name OR last name
            # contains the search query. icontains is case-insensitive.
            queryset = queryset.filter(
                Q(f_name__icontains=query) | Q(lname__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        """
        Pass the search query back to the template for display.
        """
        context = super().get_context_data(**kwargs)
        # Pass the search query back to the template
        context['search_query'] = self.request.GET.get('q', '')
        return context

# CREATE VIEW
class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

# UPDATE VIEW
class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

# DELETE VIEW
class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'students/student_delete_confirm.html'
    success_url = reverse_lazy('student_list')
    
    
    
    
def custom_404_view(request, exception):
    """
    Renders the 404.html template when a page is not found.
    The 'exception' variable is passed by Django but we don't need to use it here.
    """
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    """
    Renders the 500.html template for internal server errors.
    """
    return render(request, 'errors/500.html', status=500)



def trigger_error_view(request):
    # This will cause a ZeroDivisionError
    result = 1 / 0
    return render(request, 'some_template.html')