from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

# WTForm


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

# CREATE A FORM FOR USER DATA


class RegisterForm(FlaskForm):
    email = EmailField(label="Email: ", validators=[DataRequired()])
    name = StringField(label="Name: ", validators=[DataRequired()])
    password = PasswordField(label='Password: ', validators=[DataRequired()])
    sign_up_button = SubmitField('Sign Up')

# CREATE A FORM FOR LOGINING IN


class LoginForm(FlaskForm):
    email = EmailField(label="Email: ",  validators=[DataRequired()])
    password = PasswordField(label="Password: ", validators=[DataRequired()])
    login_button = SubmitField(label="Log in")

# CREATE A FORM FOR COMMENTING


class CommentForm(FlaskForm):
    comment_text = CKEditorField(label='Comment', validators=[DataRequired()])
    submit_button = SubmitField(label='Submit')
