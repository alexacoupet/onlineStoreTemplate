#!/usr/bin/env python3

from authentication.auth_tools import login_pipeline, update_passwords, hash_password
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from flask import session

from database.db import Database
from flask import Flask, render_template, request, url_for, redirect, session
from core.session import Sessions
import random
import string
import os
import hashlib
from flask import flash, redirect, url_for
import os
import shutil
from datetime import datetime
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
HOST, PORT = 'localhost', 8080
global username, products, db, sessions
username = 'default'
db = Database('database/store_records.db')
products = db.get_full_inventory()
sessions = Sessions()
sessions.add_new_session(username, db)

BACKUP_DIR = 'database/backups'


@app.route('/')
def homepage():
    """
    Renders the homepage. If a user is logged in, it'll show their information, otherwise the general landing page.
    """
    if 'username' in session:
        return render_template('home.html', products=products, username=session['username'], current_path=request.path)
    else:
        return render_template('index.html', products=products, current_path=request.path)

@app.route('/login')
def login_page():
    """
    Renders the login page when the user is at the `/login` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('login.html', current_path=request.path, sessions=sessions)


# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# ||                                                                                                                       ||
# ||                                                                                                                       ||                   
# ||                                                                                                                       ||
# ||                              *****  Added functions and changes from Alexa Coupet *****                               ||
# ||                                                                                                                       ||
# ||                                                                                                                       ||
# ||                                                                                                                       || 
# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

@app.route('/backup', methods=['POST'])
def backup():
    """Creates a backup of the current database."""
    try:
        # Ensure backup directory exists
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        # Create a timestamped backup file name
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f'store_records_{timestamp}.db'
        backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

        # Copy the current database to the backup file
        shutil.copy2('database/store_records.db', backup_filepath)

        return jsonify({"status": "success", "message": f"Backup created at {backup_filepath}"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/restore', methods=['POST'])
def restore():
    """Restore the database from a given backup."""
    backup_filename = request.form.get('backup_filename')

    if not backup_filename:
        return jsonify({"status": "error", "message": "Please provide the backup filename to restore from."}), 400

    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_filepath):
        return jsonify({"status": "error", "message": "Backup file not found."}), 404

    try:
        # Replace the current database with the backup
        shutil.copy2(backup_filepath, 'database/store_records.db')
        return jsonify({"status": "success", "message": "Database restored successfully!"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def automated_backup():
    """
    Function that automatically backs up the database.
    Calls the backup() function to do the actual backup.
    """
    backup()

scheduler = BackgroundScheduler()
scheduler.add_job(func=automated_backup, trigger="interval", hours=24)
scheduler.start()

# # Register an exit function to shut down the scheduler when the app exits
atexit.register(lambda: scheduler.shutdown())

##search website function
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')  # Get the query from the URL
    if not db.is_valid_search(query):  # Check if the search query is valid
        return render_template('error.html', message='Invalid search query')
    
    results = db.db_search(query)  # Fetch the results from the database
    if not results:
        return render_template('no_results.html', message='No results found', query=query)
    return render_template('search_results.html', results=results, query=query)




# ||   Alexa's login and register function with exceptions and user checks  ||
@app.route('/home', methods=['POST'])
def login():
    """
    Renders the home page when the user is at the `/home` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - sessions: adds a new session to the sessions object
    """
    username = request.form['username']
    password = request.form['password']
    
    # Check if username exists in the database
    if not db.user_exists(username):  # Assuming you have such a method in your `db` object
        flash("Username does not exist!", "error")
        return redirect(url_for('login_page'))
    
    if not login_pipeline(username, password):  # Password is incorrect
        flash("Incorrect password for the given username.", "error")
        return redirect(url_for('login_page'))

    if login_pipeline(username, password):
        sessions.add_new_session(username, db)
        return render_template('home.html', products=products, sessions=sessions)


@app.route('/logout')
def logout():
    """
    Log out the user and redirect to the login page.

    args:
        - None

    returns:
        - Redirection to the login page

    modifies:
        - session: Removes the user's data from the Flask session.
    """
    username = session.get('username')
    if username and sessions.is_active(username):
        sessions.remove_session(username)
        flash("You've been logged out!", "success")
    else:
        flash("You're not logged in!", "error")
    return redirect(url_for('login_page'))



@app.route('/register')
def register_page():
    """
    Renders the register page when the user is at the `/register` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('register.html', current_path=request.path)


@app.route('/register', methods=['POST'])
def register():
    """
    Renders the index page when the user is at the `/register` endpoint with a POST request.

    args:
        - None

    returns:
        - Redirect or rendered template

    modifies:
        - passwords.txt: adds a new username and password combination to the file
        - database/store_records.db: adds a new user to the database
    """
    # Sanitize inputs
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    email = request.form['email'].strip()
    first_name = request.form['first_name'].strip()
    last_name = request.form['last_name'].strip()

    # Check for empty fields
    if not (username and password and email and first_name and last_name):
        flash("All fields must be filled out!", "error")
        return redirect(url_for('register'))
    
    # Check if the email already exists
    if db.email_exists(email):
        flash("An account with this email already exists!", "error")
        return redirect(url_for('register'))
    
    # Check if the user already exists
    if db.user_exists(username):
        flash("User already exists!", "error")
        return redirect(url_for('register'))
    
    try:
        salt, key = hash_password(password)
        update_passwords(username, key, salt)
        db.insert_user(username, key, email, first_name, last_name)
        flash('Registration successful! Please login.', 'success')
        return render_template('index.html')

    except Exception as e:
        print(e)
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for('register_page'))



@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Renders the checkout page when the user is at the `/checkout` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - sessions: adds items to the user's cart
    """
    order = {}
    user_session = sessions.get_session(username)
    for item in products:
        print(f"item ID: {item['id']}")
        if request.form[str(item['id'])] > '0':
            count = request.form[str(item['id'])]
            order[item['item_name']] = count
            user_session.add_new_item(
                item['id'], item['item_name'], item['price'], count)

    user_session.submit_cart()

    return render_template('checkout.html', order=order, sessions=sessions, total_cost=user_session.total_cost, current_path=request.path)




#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
#                          ||   Added functions and changes from Jack Eliseo   ||
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------


app.secret_key = os.environ.get('SECRET_KEY', 'f89049a8cc4bda8828ad76eb822ae791')



#Route to newpassword.html
@app.route('/newpassword', methods=['GET'])
def newpassword():
    return render_template('newpassword.html')

#Route to good_email.html
@app.route('/good_email')
def good_email():
    return render_template('good_email.html')


#Route to bad_email.html
@app.route('/bad_email')
def bad_email():
    email = session.get('reset_email')
    return render_template('bad_email.html')


#Creation of random 6 digit code user will need to copy for password reset 
def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

#Handles which html page the user will be redirected towards either good_email or bad_email
#Also stores the six digit random code and email within the session
@app.route('/password_reset', methods=['POST'])
def password_reset():
    """
    Handles the password reset form submission.

    Args:
        - None

    Returns:
        - If the email exists in the database, redirects to the good_email.html page.
        - If the email does not exist in the database, redirects to the bad_email.html page.
    """
    email = request.form['email']

    # Check if the email exists in the database
    if db.is_valid_email_in_database(email):
        # Email is valid, generate the random 6-digit code
        code = generate_random_string(6)

        # Store the code and email in the session
        session['reset_code'] = code
        session['reset_email'] = email

        # Redirect to good_email.html
        return redirect(url_for('good_email'))
    else:
        # Email is not valid, redirect to bad_email.html
        return redirect(url_for('bad_email'))




@app.route('/password_confirmation', methods=['GET', 'POST'])
def password_confirmation():
    """
    Renders the password confirmation page when the user is at the `/password_confirmation` endpoint.

    Returns:
        - If the user enters the correct code, redirects to the `confirm_password_reset` route.
        - If the user enters an incorrect code or the page is accessed via GET, renders the `password_confirmation.html` template.
    """
    if request.method == 'POST':
        entered_code = request.form['code']
        if 'reset_code' in session and session['reset_code'] == entered_code:
            # Redirect to confirm_password_reset.html
            return redirect(url_for('confirm_password_reset'))
        else:
            # Incorrect code entered, show password_confirmation.html again
            return render_template('password_confirmation.html', error=True, email=session.get('reset_email'))
    else:
        # Render the password_confirmation.html template for GET requests
        return render_template('password_confirmation.html', email=session.get('reset_email'))


@app.route('/password_change_success')
def password_change_success():
    """
    Renders the password change success page when the user successfully changes their password.

    Returns:
        - None
    """
    return render_template('password_change_success.html')

@app.route('/confirm_password_reset', methods=['GET', 'POST'])
def confirm_password_reset():
    if request.method == 'POST':
        entered_code = request.form.get('passcode')  # Use 'passcode' key to get the user-entered passcode

        # Check if the entered code matches the stored code
        if 'reset_code' in session and session['reset_code'] == entered_code:
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            # Check if passwords match and meet the limit (at least 12 characters)
            if new_password == confirm_password and len(new_password) >= 12:
                # Redirect to password_change_success.html if passwords match and meet the limit
                return redirect(url_for('password_change_success'))
            elif new_password != confirm_password:
                # Render the confirm_password_reset.html template with an error message
                error_message = "Passwords do not match."
                return render_template('confirm_password_reset.html', error_message=error_message)
            else:
                # Render the confirm_password_reset.html template with an error message
                error_message = "Password should be at least 12 characters long."
                return render_template('confirm_password_reset.html', error_message=error_message)
        else:
            # Incorrect code entered or 'reset_code' not in session, show confirm_password_reset.html again with the entered email
            error_message = "Incorrect code entered."
            return render_template('confirm_password_reset.html', error_message=error_message, email=session.get('reset_email'))
    else:
        # Render the confirm_password_reset.html template for GET requests
        return render_template('confirm_password_reset.html', email=session.get('reset_email'))





if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
