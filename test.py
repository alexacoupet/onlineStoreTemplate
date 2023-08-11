from app import app, sessions
from app import app, db, sessions, BACKUP_DIR
import shutil
import os
from datetime import datetime


def test_logout_route():
    """
    Tests the logout route functionality.
    
    returns:
        - tuple with the first element being True if the test passes and False otherwise, and the second element being a string message indicating the test result.
    """
    # Setting up Flask test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Simulating a logged in user
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        # Assuming there's an add_new_session method in your 'sessions' module
        sessions.add_new_session('testuser')  

    # Call logout route
    response = client.get('/logout', follow_redirects=True)

    if "You've been logged out!" not in response.data.decode('utf-8'):
        return False, "Failed: User not logged out successfully."

    if sessions.is_active('testuser'):  # Assuming there's an is_active method
        return False, "Failed: User session still active after logout."

    response = client.get('/logout', follow_redirects=True)
    if "You're not logged in!" not in response.data.decode('utf-8'):
        return False, "Failed: Incorrect message when logging out without being logged in."

    return True, "Passed: Logout route works as expected."

def test_backup_route():
    """Tests the backup functionality."""
    app.config['TESTING'] = True
    client = app.test_client()
    
    response = client.post('/backup')
    data = response.get_json()

    if data['status'] != "success":
        return False, "Failed: Backup not successful."

    if not os.path.exists(data['message'].split('at ')[-1]):
        return False, "Failed: Backup file not created."

    return True, "Passed: Backup route works as expected."

def test_restore_route():
    """Tests the restore functionality."""
    app.config['TESTING'] = True
    client = app.test_client()

    backup_filename = "backup.db"  
    response = client.post('/restore', data={'backup_filename': backup_filename})
    data = response.get_json()

    if data['status'] != "success":
        return False, f"Failed: Restore not successful. Message: {data['message']}"

    return True, "Passed: Restore route works as expected."

def test_search_route():
    """Tests the search functionality."""
    app.config['TESTING'] = True
    client = app.test_client()

    query = "apple"  
    response = client.get(f'/search?q={query}')
    
    if "No results found" in response.data.decode('utf-8'):
        return False, "Failed: Valid product not found."

    return True, "Passed: Search route works as expected."

def test_login_route():
    """Tests the login functionality."""
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post('/home', data={'username': 'testuser', 'password': 'password123'})

    if "Incorrect password for the given username." in response.data.decode('utf-8'):
        return False, "Failed: Unable to login with valid credentials."

    return True, "Passed: Login route works as expected."
