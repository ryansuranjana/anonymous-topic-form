from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=16)])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=16)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6, max=16)])
    submit = SubmitField('Register')