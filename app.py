from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from flask_mail import Mail, Message
from flask_migrate import Migrate
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    code_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# Password generator function
def generate_password(selected_interests):
    first_words = ["ILike", "ILove", "IEnjoy"]
    second_words = ["Enjoy", "Watch", "Like", "Play", "Love"]
    third_words = ["Enjoy", "Watch", "Like", "Play"]

    first_word = random.choice(first_words)
    second_word = random.choice(second_words)
    third_word = random.choice(third_words)

    interest1, interest2, interest3 = selected_interests
    base_password = f"{first_word}{interest1}{second_word}{interest2}{third_word}{interest3}"

    special_characters = string.punctuation
    random_special = random.choice(special_characters)
    random_number = random.randint(0, 9)

    password = f"{base_password}{random_special}{random_number}"
    password = ''.join(random.sample(password, len(password)))

    return password

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        # Validate password
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password):
            flash('Password must be at least 8 characters long, include a number, and an uppercase letter.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        verification_code = str(random.randint(100000, 999999))
        user.verification_code = verification_code
        user.code_expiration = datetime.now() + timedelta(minutes=10)

        # Add user to database
        db.session.add(user)
        db.session.commit()

        # Send verification email
        msg = Message('Verify Your Account', sender='your_email@gmail.com', recipients=[email])
        msg.body = f'Your verification code is {verification_code}. This code expires in 10 minutes.'
        mail.send(msg)

        flash('A verification email has been sent. Please check your inbox.', 'info')
        return redirect(url_for('verify_email'))

    return render_template('register.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form['email']
        code = request.form['code']
        user = User.query.filter_by(email=email).first()

        if user and user.verification_code == code and datetime.now() < user.code_expiration:
            user.is_verified = True
            user.verification_code = None
            user.code_expiration = None
            db.session.commit()
            flash('Your account has been verified!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')

    return render_template('verify.html')

@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
