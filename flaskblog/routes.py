import secrets, os
from PIL import Image
from flaskblog import app, db, bcrypt
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog.forms import RegistrationForm, LoginForm, UpdateForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all() # to access all the posts from the database
    return render_template('home.html', posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_passowrd = bcrypt.generate_password_hash(form.password.data).decode('utf-8') #we hash the pw
        user = User(username=form.username.data, email=form.email.data, password=hashed_passowrd)
        db.session.add(user) # adding the form entries along with hashed password in the db
        db.session.commit()
        flash("Your account has been created, you can now log in", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: #if user is logged in, any request to login page should redirect to home
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit(): #Login validation
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data) #just in case if we want to save the user
            next_page = request.args.get('next') # if user tries to access anything which requires login access prior to actually logging in
            flash('You have been logged in!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful, incorrect Email or password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user() # Simply logs user out
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8) # random string generator which will become the name of the image file
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) 

    output_size = (125, 125) # image resizing and uploading
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account(): 
    form = UpdateForm() # Since we want users to have access to changing their info
    if form.validate_on_submit():
        if form.picture.data: # in case of a picture upload/change
            picture_file = save_picture(form.picture.data) # we pass the picture in our save_picture function
            current_user.image_file = picture_file # simple change the values in the db for the user
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username # by default it displays the current username/email in the form
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file) # since we want our picture to be displayed on the page
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit(): # the values align to that of the database table/collection
        post = Post(title=form.title.data, content=form.content.data, author=current_user) 
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route('/post/<int:post_id>')
def post(post_id): 
    post = Post.query.get_or_404(post_id) # to access one specific post
    return render_template('post.html', title=post.title, post=post)


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user: # user can only update their posts
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')