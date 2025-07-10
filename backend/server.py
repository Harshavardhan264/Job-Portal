from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid
import jwt
import hashlib
import logging
from pathlib import Path
from dotenv import load_dotenv
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Job Portal API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

# Create upload directory
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Models
class UserRole(str):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    ADMIN = "admin"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    role: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: str
    requirements: List[str] = []
    job_type: str = "full-time"  # full-time, part-time, contract, internship
    employer_id: str
    posted_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: str
    requirements: List[str] = []
    job_type: str = "full-time"

class Resume(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Application(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    candidate_id: str
    resume_id: str
    cover_letter: Optional[str] = None
    status: str = "pending"  # pending, reviewed, accepted, rejected
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class ApplicationCreate(BaseModel):
    job_id: str
    resume_id: str
    cover_letter: Optional[str] = None

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Job Portal API is running"}

# Authentication endpoints
@api_router.post("/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user.dict()}

@api_router.post("/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {"access_token": access_token, "token_type": "bearer", "user": User(**user).dict()}

@api_router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Job endpoints
@api_router.post("/jobs")
async def create_job(job_data: JobCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can create jobs")
    
    job_dict = job_data.dict()
    job_dict["employer_id"] = current_user.id
    job = Job(**job_dict)
    
    await db.jobs.insert_one(job.dict())
    return job

@api_router.get("/jobs")
async def get_jobs(skip: int = 0, limit: int = 50, search: Optional[str] = None):
    query = {"is_active": True}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}}
        ]
    
    jobs = await db.jobs.find(query).skip(skip).limit(limit).to_list(limit)
    return [Job(**job) for job in jobs]

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id, "is_active": True})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job)

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, job_data: JobCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can update jobs")
    
    job = await db.jobs.find_one({"id": job_id, "employer_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": job_data.dict()}
    )
    
    updated_job = await db.jobs.find_one({"id": job_id})
    return Job(**updated_job)

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can delete jobs")
    
    job = await db.jobs.find_one({"id": job_id, "employer_id": current_user.id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": {"is_active": False}}
    )
    
    return {"message": "Job deleted successfully"}

# Resume endpoints
@api_router.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can upload resumes")
    
    # Check file type
    if not file.content_type.startswith(('application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')):
        raise HTTPException(status_code=400, detail="Only PDF and Word documents are allowed")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    filename = f"{current_user.id}_{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save resume record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path)
    )
    
    await db.resumes.insert_one(resume.dict())
    return resume

@api_router.get("/resumes")
async def get_user_resumes(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can view resumes")
    
    resumes = await db.resumes.find({"user_id": current_user.id}).to_list(100)
    return [Resume(**resume) for resume in resumes]

# Application endpoints
@api_router.post("/applications")
async def apply_for_job(application_data: ApplicationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can apply for jobs")
    
    # Check if job exists
    job = await db.jobs.find_one({"id": application_data.job_id, "is_active": True})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if resume exists and belongs to user
    resume = await db.resumes.find_one({"id": application_data.resume_id, "user_id": current_user.id})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Check if already applied
    existing_application = await db.applications.find_one({
        "job_id": application_data.job_id,
        "candidate_id": current_user.id
    })
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied for this job")
    
    # Create application
    application_dict = application_data.dict()
    application_dict["candidate_id"] = current_user.id
    application = Application(**application_dict)
    
    await db.applications.insert_one(application.dict())
    return application

@api_router.get("/applications")
async def get_applications(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.CANDIDATE:
        applications = await db.applications.find({"candidate_id": current_user.id}).to_list(100)
    elif current_user.role == UserRole.EMPLOYER:
        # Get applications for employer's jobs
        employer_jobs = await db.jobs.find({"employer_id": current_user.id}).to_list(100)
        job_ids = [job["id"] for job in employer_jobs]
        applications = await db.applications.find({"job_id": {"$in": job_ids}}).to_list(100)
    else:
        applications = await db.applications.find({}).to_list(100)
    
    return [Application(**app) for app in applications]

@api_router.get("/applications/{application_id}")
async def get_application(application_id: str, current_user: User = Depends(get_current_user)):
    application = await db.applications.find_one({"id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check permissions
    if current_user.role == UserRole.CANDIDATE and application["candidate_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == UserRole.EMPLOYER:
        job = await db.jobs.find_one({"id": application["job_id"], "employer_id": current_user.id})
        if not job:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return Application(**application)

@api_router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: str, 
    status: str = Form(...), 
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can update application status")
    
    application = await db.applications.find_one({"id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if employer owns the job
    job = await db.jobs.find_one({"id": application["job_id"], "employer_id": current_user.id})
    if not job:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {"status": status}
    if notes:
        update_data["notes"] = notes
    
    await db.applications.update_one(
        {"id": application_id},
        {"$set": update_data}
    )
    
    updated_application = await db.applications.find_one({"id": application_id})
    return Application(**updated_application)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()