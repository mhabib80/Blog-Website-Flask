from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_gravatar import Gravatar
import functools
from datetime import datetime as dt
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)
admin = False


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLES
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/
class Comment(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable = False)
    auth_id = db.Column(db.Integer, ForeignKey('User.id'))
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    auth_id = db.Column(db.Integer, ForeignKey('User.id')) #the (name of table).(name of column)
    comments = relationship(Comment)

    def to_dict(self):
        global cols
        cols = [col.name for col in self.__table__.columns][1:] #all except the field id, which does not exist in the Flask form
        d = {col: getattr(self, col) for col in cols}
        return d

    def update_from_dict(self, d):
        # d = {k:v if k in cols for (k,v) in d.items() }
        for k,v in d.items():
            if k in cols:
                setattr(self, k, v)


class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable = False)
    name = db.Column(db.String(1000), nullable = False)
    posts = relationship(BlogPost) #the name of the class - Blogpost
    comments = relationship(Comment, backref = 'User') #so you can get the author's name as comment.User.name


# line below is to run once
db.create_all()


def admin_only(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        if current_user.id <= 2:
            return func(*args, **kwargs)
        else:
            abort(403)
    return wrapper_decorator


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all() #print(admin, current_user)
    return render_template("index.html", all_posts=posts, admin = admin)


@app.route('/register', methods = ['POST', 'GET'])
def register():
    form = RegistrationForm()
    if User.query.filter_by(email=form.email.data).first():
        flash('This email already exists, log in instead')
        return redirect(url_for('login'))
    else:
        if form.validate_on_submit():
            password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(email=form.email.data, password = password, name = form.name.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form = form)


@app.route('/login', methods = ['POST', 'GET'])
def login():
    form = LoginForm()
    user = User.query.filter_by(email=form.email.data).first()
    if form.validate_on_submit():
        if not user:
            flash('This email does not exist. Please try again') #print(current_user.name, current_user.is_authenticated)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.id <= 2:
                global admin
                admin = True
            return redirect(url_for('get_all_posts'))
        else:
            flash('Please check your password and try again')
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    global admin
    admin = False
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods = ['POST', 'GET'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    comments = Comment.query.filter_by(post_id = requested_post.id).all()
    # Post method for adding comments
    if request.method == 'POST':
        comment = Comment(text = form.comment.data, auth_id = current_user.id, post_id = requested_post.id)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id = requested_post.id))
    return render_template("post.html", post=requested_post, admin=admin, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        with smtplib.SMTP('smtp.gmail.com', 587) as conn:
            conn.ehlo()  # to connect to that SMTP server
            conn.starttls()  # begin encryption
            conn.login(user='mhabib80@gmail.com', password='extvslwjigaiizox')  # google app-password
            conn.sendmail(from_addr=email,
                          to_addrs='mhabib80@gmail.com',
                          msg=f'Subject: New Message from {name}\n\n{message} \n\n {name} \n {phone}')

        return render_template('contact.html', name=name, email=email, phone=phone, message=message)

    else:
        return render_template('contact.html')
    return render_template("contact.html")


@app.route("/new-post",  methods = ['POST', 'GET'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        blog_data = {k:v for (k,v) in request.form.to_dict().items() if k in BlogPost.__table__.columns }
        blog_data['date'] = dt.now().strftime('%B %d, %Y')
        blog_data['auth_id'] = current_user.id
        blog_data['author'] = current_user.name
        new_post = BlogPost(**blog_data)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods = ['POST', 'GET'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    data = post.to_dict()
    form = CreatePostForm(**data)
    if form.validate_on_submit(): # print(form.data)
        post.update_from_dict(form.data)
        db.session.commit()
        return redirect(url_for('show_post', post_id = post_id))
    else:
        return render_template('make-post.html', form = form, header = 'Edit Post')


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
