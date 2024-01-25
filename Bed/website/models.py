from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import MultipleFileField
from sqlalchemy.orm import relationship



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    citizenship = db.Column(db.String(50))
    photo = db.Column(db.String(150))
    blogs = db.relationship('Blog', back_populates='author')
    houses = db.relationship('House', back_populates='user')
    bookings = db.relationship('Booking', back_populates='user')

    def __repr__(self):
        return f"User('{self.email}', '{self.first_name}')"

class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_name = db.Column(db.String(100), nullable=False)
    owner = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    price = db.Column(db.String(20), nullable=False)
    menu = db.Column(db.Text)
    street = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False) 
    average_rating = db.Column(db.Float, default=5.0)# Add this line for the location attribute
    description = db.Column(db.Text)
    photos = db.relationship('HousePhoto', back_populates='house')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='houses')
    blogs = db.relationship('Blog', back_populates='house')
    bookings = db.relationship('Booking', back_populates='house')

    def __repr__(self):
        return f"House('{self.location}', '{self.owner}', '{self.price}', '{self.description}')"

    
class HouseForm(FlaskForm):
    house_name = StringField('House Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    price = IntegerField('Price', validators=[DataRequired()])
    menu = TextAreaField('Menu', validators=[Length(max=500)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only, please.')])
    street = StringField('Street', validators=[DataRequired(), Length(max=100)])
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)    

class HousePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)
    house = db.relationship('House', back_populates='photos')

    def __repr__(self):
        return f"HousePhoto('{self.filename}')"

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_image = db.Column(db.String(255))
    blog_text = db.Column(db.Text, nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='blogs')
    author_name = db.Column(db.String(100), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'))
    house = db.relationship('House', back_populates='blogs')

    def __repr__(self):
        return f"Blog('{self.title}', '{self.content}', '{self.rating}', '{self.date}')"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='bookings')
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'))
    house = db.relationship('House', back_populates='bookings')