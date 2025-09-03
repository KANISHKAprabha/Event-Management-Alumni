from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_registration_email(self, user_id, event_id):
    """
    Task: send registration email to the user for the event.
    Retries up to 3 times on exception.
    """
    try:
        from django.apps import apps
        User = get_user_model()
        Event = apps.get_model("events", "Event")
        user = User.objects.get(pk=user_id)
        event = Event.objects.get(pk=event_id)

        if not user.email:
            logger.warning("User %s has no email; skipping registration email.", user_id)
            return "no-email"

        subject = f"Registration confirmed — {event.name}"
        context = {"user": user, "event": event}
        text_body = render_to_string("events/registration.txt", context)
        html_body = render_to_string("forms/register_email.html", context)

        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info("Registration email sent to %s for event %s", user.email, event_id)
        return "sent"

    except Exception as exc:
        logger.exception("Failed to send registration email for user %s event %s", user_id, event_id)
        # retry on transient errors
        raise self.retry(exc=exc)



# events/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import Payment, Order  # adjust import if app name different

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Spacer, Table, TableStyle


def create_payment_pdf_bytes(payment, order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ===== Margins =====
    margin_x, margin_y = 25 * mm, 25 * mm
    content_width = width - 2 * margin_x
    y = height - margin_y

    # ===== Theme colors (from your base.html CSS vars) =====
    primary = colors.HexColor("#4e73df")
    secondary = colors.HexColor("#1cc88a")
    accent = colors.HexColor("#36b9cc")
    dark = colors.HexColor("#171819")
    gray = colors.HexColor("#666262")
    white = colors.HexColor("#ffffff")

    # ===== Header =====
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(primary)
    c.drawString(margin_x, y, "🎓 Payment Receipt")
    y -= 20

    # Draw underline
    c.setStrokeColor(secondary)
    c.setLineWidth(2)
    c.line(margin_x, y, margin_x + 200, y)
    y -= 30

    # ===== Card-like box =====
    card_height = 120
    c.setFillColor(white)
    c.setStrokeColor(accent)
    c.setLineWidth(1)
    c.roundRect(
        margin_x,
        y - card_height,
        content_width,
        card_height,
        radius=10,
        stroke=1,
        fill=1,
    )

    # Inside card padding
    text_x = margin_x + 15
    text_y = y - 25

    c.setFont("Helvetica", 12)
    c.setFillColor(dark)
    c.drawString(text_x, text_y, f"Order ID: {getattr(order, 'provider_order_id', '')}")
    text_y -= 18
    c.drawString(text_x, text_y, f"Payment ID: {getattr(order, 'payment_id', '')}")
    text_y -= 18
    c.drawString(text_x, text_y, f"Amount: ₹{payment.amount}")
    text_y -= 18

    user_obj = getattr(payment, "user", None)
    user_email = getattr(user_obj, "email", "") if user_obj else ""
    username = getattr(user_obj, "username", str(user_obj)) if user_obj else getattr(order, "user_name", "")
    c.drawString(text_x, text_y, f"Paid by: {username} ({user_email})")

    # ===== Footer =====
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(gray)
    c.drawCentredString(width / 2, margin_y / 2, "Thank you for your payment!")

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_payment_receipt_email(self, payment_id, order_id):
    """
    Celery task: generate PDF receipt and send email with attachment.
    Called from your callback view after payment is verified.
    """
    try:
        
        print(f"EMAIL_HOST_USER from settings: {settings.EMAIL_HOST_USER}")
        payment = Payment.objects.get(pk=payment_id)
        order = Order.objects.get(pk=order_id)

        # Build PDF
        pdf_bytes = create_payment_pdf_bytes(payment, order)

        # Email content
        subject = f"Receipt for Order {getattr(order, 'provider_order_id', order.pk)}"
        # Plain-text body using a template (create events/templates/emails/payment_receipt.txt)
        try:
            body = render_to_string('emails/payment_receipt.txt', {'payment': payment, 'order': order})
        except Exception:
            body = f"Please find attached the receipt for your payment of ₹{payment.amount}."

        # recipient
        recipient_email = None
        if getattr(payment, 'user', None) and getattr(payment.user, 'email', None):
            recipient_email = payment.user.email
        elif getattr(order, 'user_name', None) and hasattr(order.user_name, 'email'):
            recipient_email = order.user_name.email

        if not recipient_email:
            raise ValueError("No email address found for payment/user")

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        filename = f"receipt_{getattr(order, 'provider_order_id', order.pk)}.pdf"
        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)

        # Mark payment as emailed (optional status field)
        payment.status = getattr(payment, 'status', 'success')
        # you may want a dedicated field/payment.status choices like 'pending','success','emailed','failed'
        # only set if you have the field
        if hasattr(payment, 'status'):
            payment.status = 'emailed'
            payment.save(update_fields=['status'])

        return True
    except Exception as exc:
        # update payment status if possible
        try:
            p = Payment.objects.get(pk=payment_id)
            if hasattr(p, 'status'):
                p.status = 'email_failed'
                p.save(update_fields=['status'])
        except Exception:
            pass
        # retry the task (will raise and Celery will retry)
        raise self.retry(exc=exc)

import pandas as pd
from celery import shared_task
from django.db import transaction
from .models import Student
import traceback # Import the traceback module for detailed error logging

@shared_task
def import_students_from_excel(file_path):
    """
    Reads a large CSV safely:
    - Reads in chunks
    - Includes a detailed debug mode for troubleshooting.
    """
    
    # --- START: DEBUGGING CONFIGURATION ---
    # Set this to False when you are done debugging to reduce log noise.
    DEBUG_MODE = True 
    # The number of processed rows to show in detail in the log.
    DEBUG_LOG_LIMIT = 5 
    # --- END: DEBUGGING CONFIGURATION ---

    try:
        if not file_path.lower().endswith(".csv"):
            return f"❌ Invalid file type. Expected .csv, got {file_path}"

        chunk_size = 5000
        batch_size = 1000
        total_imported = 0
        
        # --- Variables for managing debug output ---
        is_first_chunk = True
        processed_rows_logged = 0

        print(f"Starting import for file: {file_path}")

        for chunk_index, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, dtype=str, encoding="latin1", keep_default_na=False)):
            chunk.columns = chunk.columns.str.strip().str.lower()

            # --- DEBUG [1]: Print processed column headers ONCE ---
            if is_first_chunk and DEBUG_MODE:
                print("\n--- [DEBUG] DETECTED COLUMN HEADERS (lowercase & stripped) ---")
                print("Please ensure these match the keys used in 'row.get()' below.")
                print(list(chunk.columns))
                print("-----------------------------------------------------------\n")
                is_first_chunk = False

            students_to_create = []
            
            for row_index, row in chunk.iterrows():
                # The actual row number in the CSV file
                csv_row_number = (chunk_index * chunk_size) + row_index + 2

                # --- Create the Student object ---
                student_data = {
                    'roll_no': row.get("roll number", "").strip(),
                    'f_name': row.get("first name", "").strip(),
                    'lname': row.get("last name", "").strip(),
                    'department': row.get("dept", "").strip(),
                    'current_location': row.get("current location", "").strip(),
                    'current_company': row.get("current company", "").strip(),
                    'position': row.get("current position/designation", "").strip(),
                    'job_domain': row.get("job domain", "").strip(),
                    'phone_number': row.get("mobile1", "").strip(),
                    'phone_number2': row.get("mobile2", "").strip(),
                    'personal_email_id': row.get("personal email", "").strip(),
                    'official_email_id': row.get("official email", "").strip(),
                    'linkedin_link': row.get("linkedin", "").strip(),
                }
                student = Student(**student_data)
                
                # --- DEBUG [2]: Log the first few processed student objects ---
                if DEBUG_MODE and processed_rows_logged < DEBUG_LOG_LIMIT:
                    print(f"✅ PROCESSING CSV Row #{csv_row_number}...")
                    print(f"   -> Data read: {student_data}")
                    processed_rows_logged += 1

                students_to_create.append(student)

            if students_to_create:
                with transaction.atomic():
                    Student.objects.bulk_create(
                        students_to_create, 
                        batch_size=batch_size, 
                        ignore_conflicts=True
                    )
                total_imported += len(students_to_create)

        final_message = f"✅ Import finished. Imported {total_imported} students."
        print(final_message)
        return final_message

    except Exception as e:
        # --- DEBUG [3]: Log the full error traceback for unexpected errors ---
        print(f"❌ An unexpected error occurred during import: {str(e)}")
        # This will print the full error details to your Celery worker console
        traceback.print_exc()
        return f"❌ An unexpected error occurred. See logs for details. Error: {str(e)}"


