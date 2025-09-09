# DeepXRAY - AI-Powered X-ray Analysis Platform

DeepXRAY is a cutting-edge medical imaging platform that leverages artificial intelligence to assist healthcare professionals in analyzing X-ray images. Built with Django and integrated with TensorFlow for deep learning capabilities, it provides accurate, real-time analysis of chest X-rays for pneumonia detection and other abnormalities.

## Features

### 🤖 AI-Powered Analysis
- Advanced deep learning algorithms analyze X-ray images with high accuracy
- Real-time processing with results in seconds
- Pneumonia detection and abnormality identification
- Confidence scoring for each analysis

### 👥 Multi-User Support
- **Clinicians**: Upload and analyze X-ray images
- **Radiologists**: Review and validate AI analysis results
- **Receptionists**: Manage patient information and workflow

### 📊 Comprehensive Reporting
- Detailed analysis reports with confidence scores
- Clinical findings and recommendations
- Patient history and case management
- Export capabilities for medical records

### 🔒 Security & Compliance
- HIPAA-compliant data handling
- Secure file uploads and encrypted storage
- Role-based access control
- Audit trails for all activities

## Technology Stack

- **Backend**: Django 4.2.1 with Django REST Framework
- **AI/ML**: TensorFlow 2.13.0 with Keras
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Image Processing**: Pillow (PIL)
- **API**: RESTful API with CORS support

## Installation

### Prerequisites
- Python 3.9+
- pip
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deepxray
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main site: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/
   - Detection app: http://localhost:8000/detection/

## Usage

### Getting Started

1. **Register an Account**
   - Visit the registration page
   - Choose your role (Clinician, Radiologist, or Receptionist)
   - Provide your clinic/hospital information

2. **Login to Dashboard**
   - Access the detection dashboard
   - View recent uploads and analysis results
   - Navigate through different sections

3. **Upload X-ray Images**
   - Select a patient from the dropdown
   - Upload X-ray image (drag & drop or browse)
   - Choose body part and priority level
   - Add clinical notes if needed

4. **AI Analysis**
   - Images are automatically analyzed upon upload
   - View real-time analysis results
   - Review diagnosis, confidence score, and recommendations

5. **Patient Management**
   - Register new patients
   - View patient history
   - Track analysis progress

### API Endpoints

#### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

#### X-ray Analysis
- `POST /api/upload/` - Upload X-ray image
- `POST /api/analyze/` - Run AI analysis
- `GET /api/results/` - Get analysis results

#### Patient Management
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create patient
- `GET /api/patients/{id}/` - Get patient details

## AI Model Integration

The platform integrates with a pre-trained pneumonia detection model (`pneumonia.h5`). The AI analysis includes:

1. **Image Preprocessing**
   - Resize to 224x224 pixels
   - Normalize pixel values
   - Convert to RGB format

2. **Model Prediction**
   - Load pre-trained CNN model
   - Run inference on preprocessed image
   - Generate confidence score

3. **Result Interpretation**
   - Determine diagnosis based on confidence threshold
   - Generate clinical findings
   - Provide treatment recommendations

## Configuration

### Environment Variables
```bash
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=your-secret-key
```

### Database Configuration
The default configuration uses SQLite for development. For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'deepxray_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## File Structure

```
deepxray/
├── main/                   # Django project settings
├── home/                   # Home app (landing page)
├── detection/              # Main detection app
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── ai_analysis.py     # AI integration
│   └── urls.py            # URL routing
├── templates/              # HTML templates
├── static/                 # Static files
├── media/                  # Uploaded files
├── uploads/                # X-ray images
└── requirements.txt        # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Acknowledgments

- Built with Django and TensorFlow
- Inspired by modern medical imaging solutions
- Designed for healthcare professionals

---

**DeepXRAY** - Revolutionizing medical imaging with AI-powered analysis.
