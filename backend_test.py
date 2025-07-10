import requests
import unittest
import uuid
import os
import time
from datetime import datetime

class JobPortalAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://c4f25dc9-7997-4cde-a260-2915b9b0eca8.preview.emergentagent.com/api"
        self.candidate_token = None
        self.employer_token = None
        self.candidate_user = None
        self.employer_user = None
        self.test_job_id = None
        self.test_resume_id = None
        self.test_application_id = None
        
        # Generate unique test users
        self.timestamp = int(time.time())
        self.candidate_email = f"candidate_{self.timestamp}@test.com"
        self.employer_email = f"employer_{self.timestamp}@test.com"
        self.password = "Test123!"

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        print("✅ API root endpoint test passed")

    def test_02_register_candidate(self):
        """Test candidate registration"""
        print("\n🔍 Testing candidate registration...")
        data = {
            "email": self.candidate_email,
            "password": self.password,
            "role": "candidate",
            "full_name": "Test Candidate",
            "phone": "1234567890"
        }
        response = requests.post(f"{self.base_url}/register", json=data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("access_token", response_data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["email"], self.candidate_email)
        self.assertEqual(response_data["user"]["role"], "candidate")
        
        # Save token and user for later tests
        self.candidate_token = response_data["access_token"]
        self.candidate_user = response_data["user"]
        print("✅ Candidate registration test passed")

    def test_03_register_employer(self):
        """Test employer registration"""
        print("\n🔍 Testing employer registration...")
        data = {
            "email": self.employer_email,
            "password": self.password,
            "role": "employer",
            "full_name": "Test Employer",
            "company_name": "Test Company",
            "phone": "0987654321"
        }
        response = requests.post(f"{self.base_url}/register", json=data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("access_token", response_data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["email"], self.employer_email)
        self.assertEqual(response_data["user"]["role"], "employer")
        
        # Save token and user for later tests
        self.employer_token = response_data["access_token"]
        self.employer_user = response_data["user"]
        print("✅ Employer registration test passed")

    def test_04_login_candidate(self):
        """Test candidate login"""
        print("\n🔍 Testing candidate login...")
        data = {
            "email": self.candidate_email,
            "password": self.password
        }
        response = requests.post(f"{self.base_url}/login", json=data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("access_token", response_data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["email"], self.candidate_email)
        
        # Update token
        self.candidate_token = response_data["access_token"]
        print("✅ Candidate login test passed")

    def test_05_login_employer(self):
        """Test employer login"""
        print("\n🔍 Testing employer login...")
        data = {
            "email": self.employer_email,
            "password": self.password
        }
        response = requests.post(f"{self.base_url}/login", json=data)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("access_token", response_data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["email"], self.employer_email)
        
        # Update token
        self.employer_token = response_data["access_token"]
        print("✅ Employer login test passed")

    def test_06_get_me(self):
        """Test get current user endpoint"""
        print("\n🔍 Testing get current user endpoint...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        response = requests.get(f"{self.base_url}/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], self.candidate_email)
        print("✅ Get current user test passed")

    def test_07_create_job(self):
        """Test job creation by employer"""
        print("\n🔍 Testing job creation...")
        headers = {"Authorization": f"Bearer {self.employer_token}"}
        data = {
            "title": f"Test Job {self.timestamp}",
            "company": "Test Company",
            "location": "Remote",
            "salary_min": 50000,
            "salary_max": 100000,
            "description": "This is a test job posting",
            "requirements": ["Python", "React"],
            "job_type": "full-time"
        }
        response = requests.post(f"{self.base_url}/jobs", json=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["title"], data["title"])
        self.assertEqual(response_data["employer_id"], self.employer_user["id"])
        
        # Save job ID for later tests
        self.test_job_id = response_data["id"]
        print("✅ Job creation test passed")

    def test_08_get_jobs(self):
        """Test getting job listings"""
        print("\n🔍 Testing job listings...")
        response = requests.get(f"{self.base_url}/jobs")
        self.assertEqual(response.status_code, 200)
        jobs = response.json()
        self.assertIsInstance(jobs, list)
        
        # Check if our test job is in the list
        job_found = False
        for job in jobs:
            if job["id"] == self.test_job_id:
                job_found = True
                break
        self.assertTrue(job_found, "Test job not found in job listings")
        print("✅ Job listings test passed")

    def test_09_get_job_by_id(self):
        """Test getting a specific job by ID"""
        print("\n🔍 Testing get job by ID...")
        response = requests.get(f"{self.base_url}/jobs/{self.test_job_id}")
        self.assertEqual(response.status_code, 200)
        job = response.json()
        self.assertEqual(job["id"], self.test_job_id)
        print("✅ Get job by ID test passed")

    def test_10_update_job(self):
        """Test updating a job"""
        print("\n🔍 Testing job update...")
        headers = {"Authorization": f"Bearer {self.employer_token}"}
        data = {
            "title": f"Updated Test Job {self.timestamp}",
            "company": "Test Company",
            "location": "Remote",
            "salary_min": 60000,
            "salary_max": 120000,
            "description": "This is an updated test job posting",
            "requirements": ["Python", "React", "FastAPI"],
            "job_type": "full-time"
        }
        response = requests.put(f"{self.base_url}/jobs/{self.test_job_id}", json=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_job = response.json()
        self.assertEqual(updated_job["title"], data["title"])
        print("✅ Job update test passed")

    def test_11_upload_resume(self):
        """Test resume upload"""
        print("\n🔍 Testing resume upload...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        # Create a temporary PDF file
        temp_file_path = "/tmp/test_resume.pdf"
        with open(temp_file_path, "w") as f:
            f.write("This is a test resume")
        
        files = {"file": ("test_resume.pdf", open(temp_file_path, "rb"), "application/pdf")}
        response = requests.post(
            f"{self.base_url}/resumes/upload", 
            files=files,
            headers={"Authorization": f"Bearer {self.candidate_token}"}
        )
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        resume_data = response.json()
        self.assertEqual(resume_data["user_id"], self.candidate_user["id"])
        
        # Save resume ID for later tests
        self.test_resume_id = resume_data["id"]
        print("✅ Resume upload test passed")

    def test_12_get_resumes(self):
        """Test getting user resumes"""
        print("\n🔍 Testing get user resumes...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        response = requests.get(f"{self.base_url}/resumes", headers=headers)
        self.assertEqual(response.status_code, 200)
        resumes = response.json()
        self.assertIsInstance(resumes, list)
        
        # Check if our test resume is in the list
        resume_found = False
        for resume in resumes:
            if resume["id"] == self.test_resume_id:
                resume_found = True
                break
        self.assertTrue(resume_found, "Test resume not found in user resumes")
        print("✅ Get user resumes test passed")

    def test_13_apply_for_job(self):
        """Test applying for a job"""
        print("\n🔍 Testing job application...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        data = {
            "job_id": self.test_job_id,
            "resume_id": self.test_resume_id,
            "cover_letter": "This is a test cover letter"
        }
        response = requests.post(f"{self.base_url}/applications", json=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        application_data = response.json()
        self.assertEqual(application_data["job_id"], self.test_job_id)
        self.assertEqual(application_data["resume_id"], self.test_resume_id)
        self.assertEqual(application_data["candidate_id"], self.candidate_user["id"])
        
        # Save application ID for later tests
        self.test_application_id = application_data["id"]
        print("✅ Job application test passed")

    def test_14_get_applications_candidate(self):
        """Test getting applications as a candidate"""
        print("\n🔍 Testing get applications as candidate...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        response = requests.get(f"{self.base_url}/applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        applications = response.json()
        self.assertIsInstance(applications, list)
        
        # Check if our test application is in the list
        application_found = False
        for app in applications:
            if app["id"] == self.test_application_id:
                application_found = True
                break
        self.assertTrue(application_found, "Test application not found in candidate applications")
        print("✅ Get applications as candidate test passed")

    def test_15_get_applications_employer(self):
        """Test getting applications as an employer"""
        print("\n🔍 Testing get applications as employer...")
        headers = {"Authorization": f"Bearer {self.employer_token}"}
        response = requests.get(f"{self.base_url}/applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        applications = response.json()
        self.assertIsInstance(applications, list)
        
        # Check if our test application is in the list
        application_found = False
        for app in applications:
            if app["id"] == self.test_application_id:
                application_found = True
                break
        self.assertTrue(application_found, "Test application not found in employer applications")
        print("✅ Get applications as employer test passed")

    def test_16_get_application_by_id(self):
        """Test getting a specific application by ID"""
        print("\n🔍 Testing get application by ID...")
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        response = requests.get(f"{self.base_url}/applications/{self.test_application_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        application = response.json()
        self.assertEqual(application["id"], self.test_application_id)
        print("✅ Get application by ID test passed")

    def test_17_update_application_status(self):
        """Test updating application status"""
        print("\n🔍 Testing update application status...")
        headers = {"Authorization": f"Bearer {self.employer_token}"}
        data = {"status": "accepted"}
        response = requests.put(
            f"{self.base_url}/applications/{self.test_application_id}/status", 
            data=data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        updated_application = response.json()
        self.assertEqual(updated_application["status"], "accepted")
        print("✅ Update application status test passed")

    def test_18_delete_job(self):
        """Test deleting a job (soft delete)"""
        print("\n🔍 Testing job deletion...")
        headers = {"Authorization": f"Bearer {self.employer_token}"}
        response = requests.delete(f"{self.base_url}/jobs/{self.test_job_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        
        # Verify the job is soft deleted (is_active = False)
        response = requests.get(f"{self.base_url}/jobs/{self.test_job_id}")
        self.assertEqual(response.status_code, 404)
        print("✅ Job deletion test passed")

if __name__ == "__main__":
    # Run the tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(JobPortalAPITest("test_01_api_root"))
    test_suite.addTest(JobPortalAPITest("test_02_register_candidate"))
    test_suite.addTest(JobPortalAPITest("test_03_register_employer"))
    test_suite.addTest(JobPortalAPITest("test_04_login_candidate"))
    test_suite.addTest(JobPortalAPITest("test_05_login_employer"))
    test_suite.addTest(JobPortalAPITest("test_06_get_me"))
    test_suite.addTest(JobPortalAPITest("test_07_create_job"))
    test_suite.addTest(JobPortalAPITest("test_08_get_jobs"))
    test_suite.addTest(JobPortalAPITest("test_09_get_job_by_id"))
    test_suite.addTest(JobPortalAPITest("test_10_update_job"))
    test_suite.addTest(JobPortalAPITest("test_11_upload_resume"))
    test_suite.addTest(JobPortalAPITest("test_12_get_resumes"))
    test_suite.addTest(JobPortalAPITest("test_13_apply_for_job"))
    test_suite.addTest(JobPortalAPITest("test_14_get_applications_candidate"))
    test_suite.addTest(JobPortalAPITest("test_15_get_applications_employer"))
    test_suite.addTest(JobPortalAPITest("test_16_get_application_by_id"))
    test_suite.addTest(JobPortalAPITest("test_17_update_application_status"))
    test_suite.addTest(JobPortalAPITest("test_18_delete_job"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)