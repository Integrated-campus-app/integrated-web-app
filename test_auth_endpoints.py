import requests
import pytest

# Configuration
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/api/auth/register/"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"

# Test user data
TEST_USER = {
    "username": "test_user_1",
    "university_email": "test_user_1@astu.edu.et",
    "password": "securepassword123",
    "password2": "securepassword123"
}

def test_user_registration():
    """Test successful user registration"""
    # Clean up first by deleting if exists
    requests.delete(f"{REGISTER_URL}{TEST_USER['username']}/")
    
    response = requests.post(REGISTER_URL, json=TEST_USER)
    
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["user"]["username"] == TEST_USER["username"]
    assert response.json()["user"]["email"] == TEST_USER["university_email"]
    print("✓ Registration test passed")

def test_duplicate_registration():
    """Test duplicate user registration fails"""
    response = requests.post(REGISTER_URL, json=TEST_USER)
    assert response.status_code == 400
    assert "already exists" in str(response.json())
    print("✓ Duplicate registration test passed")

def test_invalid_email_registration():
    """Test registration with invalid email format"""
    invalid_user = TEST_USER.copy()
    invalid_user["university_email"] = "invalid_email@gmail.com"
    invalid_user["username"] = "test_user_2"
    
    response = requests.post(REGISTER_URL, json=invalid_user)
    
    assert response.status_code == 400
    assert "@astu.edu.et" in str(response.json())
    print("✓ Invalid email test passed")

def test_user_login():
    """Test successful login with credentials"""
    login_data = {
        "email": TEST_USER["university_email"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    
    assert response.status_code == 200
    assert "access" in response.json()
    assert "refresh" in response.json()
    assert response.json()["user"]["email"] == TEST_USER["university_email"]
    print("✓ Login test passed")

def test_invalid_login():
    """Test login with invalid credentials"""
    login_data = {
        "email": TEST_USER["university_email"],
        "password": "wrongpassword"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    
    assert response.status_code == 401
    assert "No active account" in str(response.json())
    print("✓ Invalid login test passed")

def test_missing_field_login():
    """Test login with missing email field"""
    login_data = {
        "password": TEST_USER["password"]
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    
    assert response.status_code == 400
    assert "This field is required" in str(response.json())
    print("✓ Missing field test passed")

if __name__ == "__main__":
    print("Running authentication tests...\n")
    test_user_registration()
    test_duplicate_registration()
    test_invalid_email_registration()
    test_user_login()
    test_invalid_login()
    test_missing_field_login()
    print("\nAll tests completed!")