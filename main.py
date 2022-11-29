from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from admin_only_decorator import admin_only


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
login_approval_bot = LoginManager()
login_approval_bot.init_app(app=app)
gravatar = Gravatar(app, size=100, rating='g', default='retro',
                    force_default=False, force_lower=False, use_ssl=False, base_url=None)


@login_approval_bot.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Connect to DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

# Configure Tables in DB


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users_data.id'))
    author = relationship('User', lazy='subquery', back_populates='posts')

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship('Comment', back_populates='parent_post')


class User(UserMixin, db.Model):
    __tablename__ = "users_data"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users_data.id'))
    comment_author = relationship('User', back_populates='comments')

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates='comments')


db.create_all()


nav_bar_rules = {
    'get_all_posts': [
        'Home', 'Register', 'Logout', 'About', 'Contact'
    ],

    'register': [
        'Home', 'Login', 'About', 'Contact'
    ],

    'login': [
        'Home', 'Register', 'About', 'Contact'
    ],

    'show_post': [
        'Home', 'Register', 'Logout', 'About', 'Contact'
    ],

    'about': [
        'Home', 'Register', 'Contact'
    ],

    'contact': [
        'Home', 'Register', 'About'
    ],

    'add_new_post': [
        'Home', 'Register', 'Logout', 'About', 'Contact'
    ],

    'edit_post': [
        'Home', 'Register', 'Logout', 'About', 'Contact'
    ],

    'find_route': {
        'Home': 'get_all_posts',
        'Register': 'register',
        'Login': 'login',
        'Logout': 'logout',
        'About': 'about',
        'Contact': 'contact'
    }
}


@app.route('/all_posts')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template(
        "index.html",
        all_posts=posts,
        logged_in=False,
        nav_bar=nav_bar_rules,
        key='get_all_posts'
    )


@app.route('/register', methods=['POST', 'GET'])
def register():

    form = RegisterForm()
    if form.validate_on_submit():
        typed_email = form.email.data

        # If email entered already exist in the DB
        if User.query.filter_by(email=typed_email).first():
            flash("This Email is already taken. Please try logging in.")
            return redirect(url_for('login'))
        else:
            password_typed = form.password.data

            # If user typed a week password
            if not len(password_typed) >= 8:
                flash(
                    "Please enter a strong password. Must contain 8 charactors or above")
                return redirect(url_for('register'))
            else:
                # Encrypting Password: Hashing and 9 rounds of salt
                hashed_salted_password = generate_password_hash(
                    password=password_typed,
                    method='pbkdf2:sha256',
                    salt_length=8
                )

                # Use form.name.data for WTForms and request.form.get('name') for HTML forms
                new_user = User(
                    name=form.name.data,
                    email=typed_email,
                    password=hashed_salted_password
                )
                db.session.add(new_user)
                db.session.commit()
                flash("Login with your new account.")
                return redirect(url_for('login'))

    return render_template(
        'register.html',
        form=form,
        nav_bar=nav_bar_rules,
        key='register'
    )


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email_entered = form.email.data
        user_here = User.query.filter_by(email=email_entered).first()

        # Email check
        if user_here:
            db_hash_password = user_here.password
            password_entered = form.password.data

            # Password check
            if check_password_hash(db_hash_password, password_entered):
                # Login the user
                login_user(user_here)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Incorrect password! Try again.")
                return redirect(url_for('login'))
        else:
            flash("Email entered does not exist.")
            return redirect(url_for('login'))

    return render_template(
        'login.html',
        form=form,
        nav_bar=nav_bar_rules,
        key='login'
    )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_required
@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please login before commenting")
            return redirect(url_for('login'))

        comment_new = Comment(
            comment_text=comment_form.comment_text.data,
            author_id=current_user.id,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(comment_new)
        db.session.commit()

    return render_template(
        "post.html",
        post=requested_post,
        form=comment_form,
        nav_bar=nav_bar_rules,
        key='show_post'
    )


@app.route("/about")
def about():
    return render_template(
        "about.html",
        nav_bar=nav_bar_rules,
        key='about'
    )


@app.route("/contact")
def contact():
    return render_template(
        "contact.html",
        nav_bar=nav_bar_rules,
        key='contact'
    )


@admin_only
@app.route("/new-post", methods=['GET', 'POST'])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template(
        "make-post.html",
        form=form,
        nav_bar=nav_bar_rules,
        key='add_new_post'
    )


@admin_only
@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template(
        "make-post.html",
        form=edit_form,
        is_edit=True,
        current_user=current_user,
        nav_bar=nav_bar_rules,
        key='edit_post'
    )


@admin_only
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
