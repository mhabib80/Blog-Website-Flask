from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import *
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    # author = StringField("Author", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class LoginForm(FlaskForm):
    email = StringField(label = 'Email', validators = [DataRequired(), Email()])
    password = PasswordField(label = 'Password', validators = [DataRequired(), Length(min=8)])
    submit = SubmitField(label='Login')


class RegistrationForm(LoginForm):
    name = StringField(label = 'Name', validators = [DataRequired()])
    submit = SubmitField(label='Register')


class CommentForm(FlaskForm):
    comment = CKEditorField("Leave a comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

