from flask import Flask, render_template, request, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import LoginForm
from werkzeug.security import generate_password_hash
from flask_mail import Mail
import pymysql
from threading import Timer
from random import randint

pymysql.install_as_MySQLdb()

pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.app_context().push()
ssl_args = {'ssl_ca': 'static/ca.pem'}
app.config['SECRET_KEY'] = 'a really really really really long secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://avnadmin:AVNS_L0R9hOLeXBv9wkirOjP@mysql-306be6a8-enactus.a' \
                                        '.aivencloud.com:26361/defaultdb?ssl_key=static/ca.pem '
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine(
    "mysql+pymysql://avnadmin:AVNS_L0R9hOLeXBv9wkirOjP@mysql-306be6a8-enactus.a.aivencloud.com:26361/defaultdb?ssl-mode=REQUIRED",
    connect_args=ssl_args)
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    login = db.Column(db.String(30), nullable=False, unique=True)
    teacher=db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)[0:15]

    def check_password(self, password):
        print(generate_password_hash(password)[0:15])
        print(self.password_hash)
        if (generate_password_hash(password)[0:15] == self.password_hash):
            return True
        return False


class usee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String(300), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    possible_days = db.Column(db.String(50), nullable=False)
    clas = db.Column(db.Integer, nullable=False)
    confirmed = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(300), default=None)
    email = db.Column(db.String(300), default=None)
    sender = db.Column(db.String(300), default=None)

    def __repr__(self):
        return '<usee %r>' % self.id


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False, unique=True)
    subjects = db.relationship('Subject', backref='class', lazy=True)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    courses = db.relationship('Course', backref='subject', lazy=True)


class randomvalue(db.Model):
    id = db.Column(db.Integer, primary_key=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f"Image('{self.filename}')"


def fake_sender(): 
    app.app_context().push()
    randomval = randint(1, 100000000)
    ide = randomvalue(id=randomval)
    print(ide)
    try:
        db.session.add(ide)
        db.session.commit()
        try:
            randomvalue.query.filter_by(id=randomval).delete()
            db.session.commit()
        except:
            print("fake_sender_commitment_error")
    except:
        print("fake_sender_db_error")


def shedule(func, nth_sec):
    now_sec = datetime.now().second
    wait = (60 + nth_sec - now_sec) % 60

    Timer(wait, func).start()
    Timer(wait + 60, lambda: shedule(func, nth_sec)).start()


shedule(fake_sender, 10)
print("ok")


@app.route("/index", methods=['GET', 'POST'])
def index():
    form = LoginForm(request.form)
    print("login opened")
    if request.method == "POST":
        print("POST")
        for l in form:
            print(l)
        print(form.errors)
        db.session.rollback()
        print("Login is being proceeded")
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            print("START")
            login_user(user)
            print("DONE")
            return redirect('/meets-subj1')
        else:
            flash('Неверный email или пароль', 'error')
    else:
        print("login wrong method")
    return render_template('index.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из аккаунта.', 'success')
    return redirect('index')

@app.route('/subjects')
@login_required
def subjects():
    classes = Class.query.all()
    return render_template('subjects.html', classes=classes)


@app.route('/notifications')
@login_required
def notifications():
    use = usee.query.order_by(usee.date.desc()).all()
    return render_template('notifications.html', use=use)


@app.route('/class/<int:class_id>/subjects')
def class_subjects(class_id):
    class_info = Class.query.get_or_404(class_id)
    subjects = class_info.subjects
    return render_template('class_subjects.html', class_info=class_info, subjects=subjects)


@app.route('/subject/<int:subject_id>')
def list_courses(subject_id):
    subject = Subject.query.get(subject_id)
    class_info = Class.query.get(subject_id)
    courses = subject.courses
    return render_template('article.html', subject=subject, courses=courses, class_info=class_info)


@app.route('/get_course_content/<int:course_id>', methods=['GET'])
def get_course_content(course_id):
    course = Course.query.get_or_404(course_id)
    description = course.description.split("/n")
    images = Image.query.filter_by(course_id=course_id).all()
    image_ids = [image.id for image in images]
    print(image_ids)
    for i, line in enumerate(description):
        while "<" in line and ">" in line:
            start_index = line.find("<")
            end_index = line.find(">")
            if start_index != -1 and end_index != -1:
                image_id_str = line[start_index + 1:end_index]

                if image_id_str.isdigit():
                    image_id = int(image_id_str)
                    if image_id in image_ids:
                        image_filename = Image.query.get(image_id).filename
                        line = line.replace(f"<{image_id_str}>",
                                            f"<img src='../../static/{image_filename}' alt='Image'>")
                        print(line)

                        description[i] = line
                    else:
                        line = line.replace(f"<{image_id_str}>", "")
                        print(1)
                else:
                    print(type(image_id_str))
                    line = line.replace(f"<{image_id_str}>", "")
    content = {
        'title': course.title,
        'description': description
    }
    print(description)
    return jsonify(content)


@app.route("/submit_link", methods=['POST'])
@login_required
def submit_link():
    if request.method == 'POST':
        link = request.form.get('form-link')

        meet_id = request.form.get('meet_id')

        meet_record = usee.query.get(meet_id)

        if meet_record:
            meet_record.link = link
            meet_record.confirmed = 1
            meet_record.sender = current_user.email
            try:
                db.session.commit()

                return jsonify({'success': True})

            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)})

        return jsonify({'success': False, 'error': 'Meeting record not found'})
    else:
        return jsonify({'success': False, 'error': 'Invalid request method'})


@app.route("/faq")
def faq():
    return render_template('faq.html')

@app.route("/meets-subj1")
@login_required
def meets1():


    if request.method == "POST":
        link = request.form['linkk']
        try:
            db.session.add(link)
            db.session.commit()
            return redirect("/meets-subj1")
        except:
            return "При добавлении ссылки произошла ошибка"
    else:
        questions = usee.query.order_by(usee.date.desc()).all()
        return render_template('meets.html', questions=questions)

@app.route("/")
@app.route("/main")
def about():
    return render_template('main.html')


@app.route("/meet-create", methods=['POST', 'GET'])
@login_required
def meet_create():
    if request.method == "POST":
        quote = request.form['quote']
        topic = request.form['topic']
        possible_days = request.form['possible_days']
        print(possible_days)
        possible_day = list(possible_days)
        possible_days = ""
        possible_day[10] = " "
        constant_user = User.query.filter_by(id=current_user.id).first()
        email = constant_user.email
        for i in possible_day:
            possible_days = possible_days + i
        clas = request.form['class']
        possible_days = possible_days + ":10"
        ides = randint(1, 1000000000)
        use = usee(id=ides, quote=quote, topic=topic, possible_days=possible_days, clas=clas, confirmed=0, email=email,
                   date=datetime.now())
        print(quote + ",", topic, possible_days, clas, email, datetime.now)
        try:
            db.session.add(use)
            db.session.commit()
            return redirect('/meets-subj1')
        except:
            return "При добавлении запроса произошла ошибка"

    else:
        return render_template('create-meet.html')

if __name__ == '__main__':
    app.run(debug=True)

