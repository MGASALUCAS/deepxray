from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import json
import base64
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from .models import UserProfile, Patient, PatientQueue, XRaySubmission, AnalysisResult, Hospital


def is_allowed(request):
    """Check if user is authenticated"""
    if request.user.is_authenticated:
        return True
    else:
        return redirect("/detection/login")


@login_required
def detection_home(request):
    """Main detection dashboard"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None
    
    # Get recent submissions for the user
    recent_submissions = XRaySubmission.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get analysis results
    analysis_results = AnalysisResult.objects.filter(
        submission__user=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'recent_submissions': recent_submissions,
        'analysis_results': analysis_results,
    }
    return render(request, 'detection/detection_home.html', context)


@login_required
def upload_xray(request):
    """X-ray upload interface"""
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            file = request.FILES.get('xray_image')
            body_part = request.POST.get('body_part', 'chest')
            priority = request.POST.get('priority', 'normal')
            clinical_notes = request.POST.get('clinical_notes', '')
            
            if not file or not patient_id:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Get or create patient
            try:
                patient = Patient.objects.get(patient_id=patient_id)
            except Patient.DoesNotExist:
                return JsonResponse({'error': 'Patient not found'}, status=404)
            
            # Create submission
            submission = XRaySubmission.objects.create(
                user=request.user,
                patient=patient,
                file_name=file.name,
                file_path=file,
                body_part=body_part,
                priority=priority,
                hospital_id=patient.hospital_id,
                status='uploaded'
            )
            
            # Update patient status
            patient.status = 'xray_uploaded'
            patient.save()
            
            return JsonResponse({
                'success': True,
                'submission_id': submission.submission_id,
                'message': 'X-ray uploaded successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Get patients for dropdown
    patients = Patient.objects.all()[:20]  # Limit for performance
    context = {
        'patients': patients,
    }
    return render(request, 'detection/upload_xray.html', context)


def login_view(request):
    """Login view for detection app"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/detection/')
        else:
            return render(request, 'detection/login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'detection/login.html')


def register_view(request):
    """Registration view for detection app"""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role', 'clinician')
            clinic_name = request.POST.get('clinic_name')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile
            UserProfile.objects.create(
                user=user,
                role=role,
                clinic_name=clinic_name
            )
            
            # Auto login
            login(request, user)
            return redirect('/detection/')
            
        except Exception as e:
            return render(request, 'detection/register.html', {
                'error': str(e)
            })
    
    return render(request, 'detection/register.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('/detection/login')


@login_required
def analyze_xray(request, submission_id):
    """Analyze X-ray using AI"""
    try:
        submission = get_object_or_404(XRaySubmission, submission_id=submission_id, user=request.user)
        
        # Check if already analyzed
        if submission.status == 'analyzed':
            existing_result = AnalysisResult.objects.filter(submission=submission).first()
            if existing_result:
                return JsonResponse({
                    'success': True,
                    'already_analyzed': True,
                    'result': {
                        'diagnosis': existing_result.diagnosis,
                        'confidence': existing_result.confidence,
                        'findings': existing_result.findings,
                        'recommendations': existing_result.recommendations,
                    }
                })
        
        # Update status to analyzing
        submission.status = 'analyzing'
        submission.save()
        
        # Run AI analysis
        file_path = submission.file_path.path
        from .ai_analysis import run_ai_analysis
        ai_result = run_ai_analysis(file_path)
        
        # Create analysis result
        analysis = AnalysisResult.objects.create(
            submission=submission,
            radiologist=request.user,
            diagnosis=ai_result['diagnosis'],
            confidence=ai_result['confidence'],
            findings=ai_result['findings'],
            recommendations=ai_result['recommendations'],
            radiologist_notes='AI Analysis completed',
            image_path=file_path
        )
        
        # Update submission status
        submission.status = 'analyzed'
        submission.save()
        
        # Update patient status
        submission.patient.status = 'analysis_completed'
        submission.patient.save()
        
        return JsonResponse({
            'success': True,
            'result': {
                'diagnosis': analysis.diagnosis,
                'confidence': analysis.confidence,
                'findings': analysis.findings,
                'recommendations': analysis.recommendations,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def analysis_results(request):
    """View analysis results"""
    results = AnalysisResult.objects.filter(
        submission__user=request.user
    ).order_by('-created_at')
    
    context = {
        'results': results,
    }
    return render(request, 'detection/analysis_results.html', context)


@login_required
def patient_management(request):
    """Patient management interface"""
    if request.method == 'POST':
        # Handle patient registration
        try:
            # Validate required fields
            required_fields = ['first_name', 'surname', 'age', 'gender', 'phone']
            missing_fields = []
            
            for field in required_fields:
                if not request.POST.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                return JsonResponse({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
            
            # Validate age
            try:
                age = int(request.POST.get('age'))
                if age < 0 or age > 120:
                    return JsonResponse({
                        'error': 'Age must be between 0 and 120'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'error': 'Age must be a valid number'
                }, status=400)
            
            # Validate gender
            gender = request.POST.get('gender')
            if gender not in ['male', 'female', 'other']:
                return JsonResponse({
                    'error': 'Invalid gender selection'
                }, status=400)
            
            patient_id = f"HOSP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4]}"
            
            patient = Patient.objects.create(
                patient_id=patient_id,
                first_name=request.POST.get('first_name'),
                second_name=request.POST.get('second_name', ''),
                surname=request.POST.get('surname'),
                age=age,
                gender=gender,
                phone=request.POST.get('phone'),
                clinical_notes=request.POST.get('clinical_notes', ''),
                hospital_id=request.POST.get('hospital_id', 'default'),
                status='registered'
            )
            
            # Add to patient queue
            PatientQueue.objects.create(
                patient=patient,
                receptionist=request.user,
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'patient_id': patient_id,
                'message': 'Patient registered successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Get patients
    patients = Patient.objects.all().order_by('-registration_date')
    context = {
        'patients': patients,
    }
    return render(request, 'detection/patient_management.html', context)


# API Views for AJAX calls
@login_required
@require_http_methods(["POST"])
def api_upload_xray(request):
    """API endpoint for X-ray upload"""
    try:
        data = json.loads(request.body)
        
        # Handle base64 image data
        if 'file_data' in data:
            file_data = base64.b64decode(data['file_data'])
            file_name = data['file_name']
            file = ContentFile(file_data, name=file_name)
        else:
            return JsonResponse({'error': 'No file data provided'}, status=400)
        
        # Get patient
        patient_id = data.get('patient_id')
        if not patient_id:
            return JsonResponse({'error': 'Patient ID required'}, status=400)
        
        try:
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)
        
        # Create submission
        submission = XRaySubmission.objects.create(
            user=request.user,
            patient=patient,
            file_name=file_name,
            file_path=file,
            body_part=data.get('body_part', 'chest'),
            priority=data.get('priority', 'normal'),
            hospital_id=patient.hospital_id,
            status='uploaded'
        )
        
        return JsonResponse({
            'success': True,
            'submission_id': submission.submission_id,
            'message': 'X-ray uploaded successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_analyze_xray(request):
    """API endpoint for X-ray analysis"""
    try:
        data = json.loads(request.body)
        submission_id = data.get('submission_id')
        
        if not submission_id:
            return JsonResponse({'error': 'Submission ID required'}, status=400)
        
        submission = get_object_or_404(XRaySubmission, submission_id=submission_id, user=request.user)
        
        # Run AI analysis
        file_path = submission.file_path.path
        from .ai_analysis import run_ai_analysis
        ai_result = run_ai_analysis(file_path)
        
        # Create analysis result
        analysis = AnalysisResult.objects.create(
            submission=submission,
            radiologist=request.user,
            diagnosis=ai_result['diagnosis'],
            confidence=ai_result['confidence'],
            findings=ai_result['findings'],
            recommendations=ai_result['recommendations'],
            radiologist_notes='AI Analysis completed',
            image_path=file_path
        )
        
        # Update submission status
        submission.status = 'analyzed'
        submission.save()
        
        return JsonResponse({
            'success': True,
            'result': {
                'diagnosis': analysis.diagnosis,
                'confidence': analysis.confidence,
                'findings': analysis.findings,
                'recommendations': analysis.recommendations,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)