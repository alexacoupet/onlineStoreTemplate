#!/usr/bin/env python3

from authentication.auth_tools import login_pipeline, update_passwords, hash_password
from database.db import Database
from flask import Flask, render_template, request, url_for, redirect, session
from core.session import Sessions
import random
import string
import os



app = Flask(__name__)
HOST, PORT = 'localhost', 8080
global username, products, db, sessions
username = 'default'
db = Database('database/store_records.db')
products = db.get_full_inventory()
sessions = Sessions()
sessions.add_new_session(username, db)


@app.route('/')
def index_page():
    """
    Renders the index page when the user is at the `/` endpoint, passing along default flask variables.

    args:
        - None

    returns:
        - None
    """
    return render_template('index.html', username=username, products=products, sessions=sessions)


@app.route('/login')
def login_page():
    """
    Renders the login page when the user is at the `/login` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('login.html')


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
    if login_pipeline(username, password):
        sessions.add_new_session(username, db)
        return render_template('home.html', products=products, sessions=sessions)
    else:
        print(f"Incorrect username ({username}) or password ({password}).")
        return render_template('index.html')


@app.route('/register')
def register_page():
    """
    Renders the register page when the user is at the `/register` endpoint.

    args:
        - None

    returns:
        - None
    """
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    """
    Renders the index page when the user is at the `/register` endpoint with a POST request.

    args:
        - None

    returns:
        - None

    modifies:
        - passwords.txt: adds a new username and password combination to the file
        - database/store_records.db: adds a new user to the database
    """
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    salt, key = hash_password(password)
    update_passwords(username, key, salt)
    db.insert_user(username, key, email, first_name, last_name)
    return render_template('index.html')


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

    return render_template('checkout.html', order=order, sessions=sessions, total_cost=user_session.total_cost)


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
                # Render the confirm_password_reset.html template with a success message
                success_message = "Passwords match and meet the 12-character requirement."
                return render_template('confirm_password_reset.html', success_message=success_message)
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
