from django.urls import path
from . import views

urlpatterns = [
     path('', views.event_overview, name='event_overview'),
   
    path('login/', views.login_view, name='login'),
    path('signup', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/create/', views.event_create, name='event_create'),
    path('event/<int:pk>/update/', views.event_update, name='event_update'),
    path('event/<int:pk>/delete/', views.event_delete, name='event_delete'),
     path('already-registered/', views.already_registered_view, name='already_registered'),
    path('overview/', views.event_overview, name='event_overview'),
    path('events/register/<int:event_id>/', views.register_event, name='register_event'),
    path('event/<int:event_pk>/agenda/create/', views.agenda_create, name='agenda_create'),
    path('agenda/<int:pk>/update/', views.agenda_update, name='agenda_update'),
    path('agenda/<int:pk>/delete/', views.agenda_delete, name='agenda_delete'),
    path('events/<int:event_pk>/beverages/add/', views.beverage_create, name='beverage_create'),
    path('beverages/<int:pk>/edit/', views.beverage_update, name='beverage_update'),
    path('beverages/<int:pk>/delete/', views.beverage_delete, name='beverage_delete'),
     path("create-form/", views.create_form, name="create_form"),
     path("form/<int:pk>/update/", views.update_form, name="update_form"),
    path("form/<int:pk>/delete/", views.delete_form, name="delete_form"),
    path("add-field/<int:form_id>/", views.add_field, name="add_field"),
    path("fill-form/<int:form_id>/", views.fill_form, name="fill_form"),
    # path("payment/<int:submission_id>/", views.payment_page, name="payment_page"),
     path("razorpay/callback/", views.callback, name="razorpay_callback"),
    # path("submissions/<int:form_id>/", views.form_submissions, name="form_submissions"),
     path("events_list_admin/", views.event_list_view, name="event_list_admin"),
    path("event/<int:event_id>/submissions/", views.event_submissions_view, name="event_submissions"),
     path("event/<int:event_id>/payments/", views.event_payments_view, name="event_payments"),
         path("upload-students/", views.upload_students, name="upload_students"),
         path("user_login/<int:event_id>/", views.user_login, name="user_login"),
          path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/add/', views.StudentCreateView.as_view(), name='student_add'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    # Add this to urlpatterns for testing
path('trigger-error/', views.trigger_error_view, name='trigger_error'),
path('event_registrations/', views.list_event_registertion, name='student_registeration_list'),

    

]
