# 📄 ResumeRanker Pro

**AI-powered resume analysis tool** that ranks candidates based on job description matching. Features user authentication, subscription tiers, and detailed skill gap analysis.

## Features
- 🔐 User authentication (login/signup)
- 📊 Resume ranking by job description relevance
- 🧠 AI-powered skill matching (TF-IDF and sBERT)
- 📈 Visual analytics with Plotly
- 💾 Analysis history tracking
- 🎚️ Subscription tier management
- 📥 CSV export functionality

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python (SQLite database)
- **NLP Libraries**: spaCy, Sentence Transformers
- **PDF Processing**: PyMuPDF, pdfplumber
- **Deployment**: Docker container

## Installation

### Prerequisites
- Python 3.9+
- pip package manager
- Docker (optional)

### Step-by-Step Setup
```bash
# Clone repository
git clone https://github.com/yourusername/ResumeRankerPro.git
cd ResumeRankerPro

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_md

# Initialize database
python database.py

# Create .env file
echo "DB_PATH=app.db" > .env
echo "SECRET_KEY=your-secret-key-here" >> .env
```

## Usage
```bash
# Start application
streamlit run app.py

# Access in browser at:
http://localhost:8501
```

## Docker Deployment
```bash
# Build Docker image
docker build -t resumeranker .

# Run container
docker run -p 8501:8501 resumeranker
```

## File Structure
```
ResumeRankerPro/
├── app.py                 # Main application
├── auth.py                # Authentication module
├── database.py            # Database operations
├── Dockerfile.dockerfile  # Docker configuration
├── .env                   # Environment variables
├── models.py              # Data models
├── README.md              # This file
├── requirements.txt       # Dependencies
├── resume_parser.py       # Resume processing
├── similarity.py          # NLP analysis
└── skills_db.txt          # Skills database
```

## Configuration
Modify these files for customization:
1. **`.env`** - Database path and secret key
2. **`skills_db.txt`** - Add custom skills for matching
3. **`database.py`** - Subscription limits and DB schema

## Troubleshooting
- **"Module not found"**: Reinstall requirements with `pip install -r requirements.txt`
- **PDF parsing errors**: Ensure PyMuPDF is installed properly
- **Authentication issues**: Verify database initialization with `python database.py`

## Support
For assistance, please contact:
[chethankaregowda@gmail.com](mailto:chethankaregowda@gmail.com)

---
**ResumeRanker Pro** © 2025 | Created with Python and Streamlit

## Key Components Explained:
1. **Authentication System** (`auth.py`):  
   - Handles user login/signup with password hashing  
   - Session management with Streamlit  

2. **Resume Parser** (`resume_parser.py`):  
   - Extracts text from PDF/DOCX files  
   - Identifies candidate names and contact info  

3. **AI Analysis** (`similarity.py`):  
   - Uses Sentence-BERT embeddings for semantic matching  
   - TF-IDF for keyword-based scoring  
   - Skill gap analysis against `skills_db.txt`  

4. **Database** (`database.py` + `models.py`):  
   - SQLite backend with 3 tables (users, jobs, analyses)  
   - Subscription tier management (Free/Pro/Enterprise)  

5. **Web Interface** (`app.py`):  
   - 4 main tabs: Analysis, History, Settings, Docs  
   - Interactive visualizations with Plotly  
   - CSV export functionality  

To run the application after setup:
```powershell
PS C:\ResumeRankerPro> venv\Scripts\activate
(venv) PS C:\ResumeRankerPro> streamlit run app.py
```
Access at: `http://localhost:8501`
