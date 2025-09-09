from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import os
import uuid


class UserProfile(models.Model):
    """Extended user profile for DeepXRAY users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('clinician', 'Clinician'),
        ('radiologist', 'Radiologist'),
        ('receptionist', 'Receptionist'),
    ], default='clinician')
    clinic_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.get_full_name()} - {self.role}'


class Patient(models.Model):
    """Patient information for X-ray analysis"""
    patient_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    phone = models.CharField(max_length=20)
    clinical_notes = models.TextField(blank=True)
    hospital_id = models.CharField(max_length=50)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=[
        ('registered', 'Registered'),
        ('clinician_review', 'Clinician Review'),
        ('checkup_completed', 'Checkup Completed'),
        ('sent_to_radiologist', 'Sent to Radiologist'),
        ('xray_uploaded', 'X-ray Uploaded'),
        ('analysis_completed', 'Analysis Completed'),
        ('results_delivered', 'Results Delivered'),
    ], default='registered')
    
    @property
    def full_name(self):
        if self.second_name:
            return f"{self.first_name} {self.second_name} {self.surname}"
        return f"{self.first_name} {self.surname}"
    
    def __str__(self):
        return f'{self.full_name} ({self.patient_id})'


class PatientQueue(models.Model):
    """Patient queue management"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    receptionist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_patients')
    status = models.CharField(max_length=30, choices=[
        ('pending', 'Pending'),
        ('clinician_assigned', 'Clinician Assigned'),
        ('checkup_completed', 'Checkup Completed'),
        ('sent_to_radiologist', 'Sent to Radiologist'),
        ('xray_uploaded', 'X-ray Uploaded'),
        ('analysis_completed', 'Analysis Completed'),
        ('results_delivered', 'Results Delivered'),
    ], default='pending')
    assigned_clinician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_patients')
    assigned_radiologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='radiologist_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.patient.full_name} - {self.status}'


def get_upload_path(instance, filename):
    """Generate upload path for X-ray images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('xray_images', filename)


def generate_submission_id():
    return f"xray_{uuid.uuid4().hex[:8]}"

class XRaySubmission(models.Model):
    """X-ray image submissions for analysis"""
    submission_id = models.CharField(max_length=50, unique=True, default=generate_submission_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to=get_upload_path)
    body_part = models.CharField(max_length=50, choices=[
        ('chest', 'Chest'),
        ('abdomen', 'Abdomen'),
        ('pelvis', 'Pelvis'),
        ('skull', 'Skull'),
        ('spine', 'Spine'),
        ('limbs', 'Limbs'),
        ('other', 'Other'),
    ], default='chest')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ], default='normal')
    hospital_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('uploaded', 'Uploaded'),
        ('pending', 'Pending'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('results_delivered', 'Results Delivered'),
    ], default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.file_name} - {self.patient.full_name}'


class AnalysisResult(models.Model):
    """AI analysis results for X-ray images"""
    submission = models.ForeignKey(XRaySubmission, on_delete=models.CASCADE)
    radiologist = models.ForeignKey(User, on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=255)
    confidence = models.FloatField()  # 0.0 to 1.0
    findings = models.TextField()
    recommendations = models.TextField()
    radiologist_notes = models.TextField(blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.diagnosis} - {self.confidence:.1%} confidence'


class Hospital(models.Model):
    """Hospital information"""
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    department = models.CharField(max_length=500)  # Comma-separated departments
    radiologists = models.CharField(max_length=500)  # Comma-separated radiologist names
    contact_info = models.JSONField()  # JSON with phone, email, address
    specialties = models.CharField(max_length=500)  # Comma-separated specialties
    
    def __str__(self):
        return self.name