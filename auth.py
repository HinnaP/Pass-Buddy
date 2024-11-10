
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, login_user, current_user, logout_user
from models import db, User
import random

auth = Blueprint('auth', __name__)
mail = Mail()

# Configure email settings
def init_mail(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
    app.config['MAIL_PASSWORD'] = 'your_email_password'
    mail.init_app(app)

# User registration route
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user = User(username=username, email=email)
        user.set_password(password)

        # Generate a verification code
        verification_code = random.randint(100000, 999999)
        user.verification_code = str(verification_code)

        db.session.add(user)
        db.session.commit()

        # Send verification email
        msg = Message('Verify Your Account', sender='your_email@gmail.com', recipients=[email])
        msg.body = f'Your verification code is {verification_code}'
        mail.send(msg)

        flash('A verification email has been sent. Please check your inbox.', 'info')
        return redirect(url_for('auth.verify_email'))

    return render_template('register.html')

# Email verification route
@auth.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        user = User.query.filter_by(email=email).first()

        if user and user.verification_code == code:
            user.is_verified = True
            db.session.commit()
            flash('Your account has been verified!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    return render_template('verify.html')

# User login route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_verified:
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please verify your email before logging in.', 'warning')
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

# User logout route
@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
