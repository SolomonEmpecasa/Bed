from flask import Blueprint, render_template, redirect, url_for, flash, request  # Make sure you import the User model
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from .models import User, House, HouseForm, HousePhoto, Blog, Event
from sqlalchemy import or_
from datetime import datetime
from . import db 
from flask_login import login_user, login_required, logout_user, current_user
from passlib.hash import sha256_crypt
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()
auth = Blueprint('auth', __name__)

UPLOAD_FOLDER = 'website/static/images'  # Specify the folder where uploads will be stored
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/')
def default():
    return redirect(url_for('auth.public_home'))

@auth.route('/public-home')
@login_required
def public_home():
    return render_template('public_home.html', user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('auth.public_home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        phone = request.form.get('phone')
        citizenship = request.form.get('citizenship')
        photo = request.files['photo'] if 'photo' in request.files else None  # Ensure 'photo' is defined
        # Check if the email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please choose a different email.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Validate other fields...

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')

        # Save additional user details
        new_user = User(
            email=email,
            first_name=first_name,
            password=hashed_password,
            phone=phone,
            citizenship=citizenship,
        )

        # Save the user's photo if it exists and is valid
        if photo and allowed_file(photo.filename):
          filename = secure_filename(photo.filename)
          photo_path = os.path.join('website', 'static', 'images', filename)
          photo.save(photo_path)
          new_user.photo = filename
        elif photo:
          flash('Invalid file type. Please upload a valid image.', category='error')

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', category='success')
        return redirect(url_for('auth.login'))

    return render_template('sign_up.html')

@auth.route('/account')
@login_required
def account():
    user_data = {
        'email': current_user.email,
        'first_name': current_user.first_name,
        'phone': current_user.phone,
        'citizenship': current_user.citizenship,
         'photo': url_for('static', filename=f'images/{current_user.photo}') if current_user.photo else None, # Assuming you stored the photo path in the database
    }
    return render_template('account.html', user=user_data)


@auth.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Delete the user account and associated data
    user_id = current_user.id
    user = User.query.get(user_id)

    if user:
        # You might want to add additional cleanup tasks here, such as deleting associated data
        db.session.delete(user)
        db.session.commit()

        flash('Your account has been deleted successfully.', category='success')
        return redirect(url_for('auth.login'))
    else:
        flash('Failed to delete account. Please try again.', category='error')
        return redirect(url_for('auth.account'))


@auth.route('/view_houses', methods=['GET', 'POST'])
def view_houses():
    search_query = request.form.get('search_query', '')
    location_filter = request.args.get('location', default='', type=str)

    if request.method == 'POST':
        houses = House.query.filter(
            or_(
                House.house_name.ilike(f'%{search_query}%'),
                House.location.ilike(f'%{search_query}%'),
                House.street.ilike(f'%{search_query}%'),
                House.description.ilike(f'%{search_query}%')
            )
        ).all()
        return render_template('search_results.html', houses=houses)

    # Fetch distinct locations for the dropdown
    distinct_locations = db.session.query(House.location).distinct().all()
    distinct_locations = [location[0] for location in distinct_locations]

    # Apply location filter if selected
    if location_filter:
        houses = House.query.filter_by(location=location_filter).all()
    else:
        houses = House.query.all()

    return render_template('view_houses.html', houses=houses, distinct_locations=distinct_locations)


@auth.route('/upload_house', methods=['GET', 'POST'])
@login_required
def upload_house():
    form = HouseForm()

    if form.validate_on_submit():
        location = form.location.data
        phone = form.phone.data
        price = form.price.data
        menu = form.menu.data
        description = form.description.data
        house_name = form.house_name.data
        street = form.street.data

        # Check if phone is provided
        if phone is None or not phone.strip():
            flash('Please provide a valid phone number.', category='error')
            return redirect(url_for('auth.upload_house'))

        new_house = House(
            house_name=house_name,
            street=street,
            location=location,
            owner=current_user.first_name,
            phone=phone,
            price=price,
            menu=form.menu.data,
            description=description,
            user_id=current_user.id
        )

        db.session.add(new_house)
        db.session.commit()

        # Handle file uploads
        for uploaded_file in form.photos.data:
            if uploaded_file:
                filename = secure_filename(uploaded_file.filename)
                photo_path = os.path.join('website', 'static', 'images', filename)
                uploaded_file.save(photo_path)

                new_photo = HousePhoto(filename=filename, house_id=new_house.id)  # Set house_id here
                db.session.add(new_photo)

        db.session.commit()

        flash('House uploaded successfully!', category='success')
        return redirect(url_for('auth.view_houses'))

    return render_template('upload_house.html', form=form)

@auth.route('/delete_house/<int:house_id>', methods=['POST'])
@login_required
def delete_house(house_id):
    house = House.query.get(house_id)
    if house and house.user_id == current_user.id:
        db.session.delete(house)
        db.session.commit()
        flash('House deleted successfully!', category='success')
    else:
        flash('Failed to delete house. Unauthorized or not found.', category='error')
    return redirect(url_for('auth.view_houses'))

@auth.route('/house_details/<int:house_id>')
@login_required
def house_details(house_id):
    house = House.query.get(house_id)
    return render_template('house_details.html', house=house)

@auth.route('/write-blog', methods=['GET', 'POST'])
@login_required
def write_blog():
    if request.method == 'POST':
        house_image = request.form.get('house_image')
        blog_text = request.form.get('blog_text')
        star_rating = request.form.get('star_rating')
        house_url = request.args.get('house_url', '')

        new_blog = Blog(
            house_image=house_image,
            blog_text=blog_text,
            star_rating=star_rating,
            user_id=current_user.id
        )
        
        new_blog.house_url = house_url

        db.session.add(new_blog)
        db.session.commit()

        flash('Blog submitted successfully!', category='success')
        return redirect(url_for('auth.blog'))

    blogs = Blog.query.all()
    return render_template('blog.html', blogs=blogs)


@auth.route('/blog')
def blog():
    blogs = Blog.query.all()
    return render_template('blog.html', blogs=blogs)


@auth.route('/delete-blog/<int:blog_id>', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if blog and blog.user_id == current_user.id:
        db.session.delete(blog)
        db.session.commit()
        flash('Blog deleted successfully!', category='success')
    else:
        flash('Failed to delete blog. Unauthorized or not found.', category='error')
    return redirect(url_for('auth.blog'))


@auth.route('/view_events')
@login_required
def view_events():
    events = Event.query.all()
    return render_template('view_events.html', events=events)

def save_image(image):
    if image:
        filename = secure_filename(image.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)
        return filepath
    return None


@auth.route('/upload_event', methods=['GET', 'POST'])
@login_required
def upload_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date_str = request.form.get('date')
        price = request.form.get('price')
        house_id = request.form.get('house_id')
        images = request.files.getlist('images')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('auth.upload_event'))

        image_paths = [save_image(image) for image in images]
        image_paths = [path for path in image_paths if path]  # Filter out None values

        new_event = Event(
            title=title,
            description=description,
            location=location,
            date=date_obj,
            price=price,
            images=image_paths,
            user_id=current_user.id,
            house_id=house_id,
            created_at=datetime.utcnow()
        )

        db.session.add(new_event)
        db.session.commit()

        flash('Event added successfully!', 'success')
        return redirect(url_for('auth.upload_event'))

    houses = House.query.all()
    return render_template('upload_event.html', houses=houses)