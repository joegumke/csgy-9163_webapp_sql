#app.py -- contains basics of python code. to start web service. 

from flask import Flask, request, redirect,render_template, session
from flask_login import LoginManager, current_user, login_user
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField, IntegerField, HiddenField
from flask_wtf import CSRFProtect
import subprocess
from datetime import *

from flask_sqlalchemy import SQLAlchemy
#pip3 install flask-sqlalchemy

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = '1234567891234567893242341230498120348719035192038471902873491283510981834712039847124123940812903752903847129038471290835710289675413864310867135'
csrf = CSRFProtect()
csrf.init_app(app)

userDict = dict()
result = ''

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class userTable(db.Model):
    username = db.Column(db.String(20), unique=True,nullable=False,primary_key=True)
    password = db.Column(db.String(60),nullable=False)
    multiFactor = db.Column(db.String(11),nullable=False)

    def __repr__(self):
        return f"userTable('{self.username}','{self.password}','{self.multiFactor}')"

class userHistory(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(userTable.username), nullable=False, primary_key=True)
    userLoggedIn = db.Column(db.DateTime, default=datetime.utcnow)
    userLoggedOut = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"userHistory('{self.userLoggedIn}','{self.userLoggedOut}')"

class RegistrationForm(Form):
    uname = StringField('Username', [validators.DataRequired(message="Enter UserName"),validators.Length(min=6, max=20)])
    pword = PasswordField('Password', [validators.DataRequired(message="Enter Password"),validators.Length(min=6, max=20)])
    mfa = StringField('2FA', [validators.DataRequired(message="Enter 10 Digit Phone Number"),validators.Length(min=11,max=11,message="Enter 11 Digit Phone Number")], id='2fa')

class wordForm(Form):
    textbox = TextAreaField('textbox', [validators.DataRequired(message="Enter Words to Check"),validators.Length(max=20000)], id='inputtext')
    
# Purging DB in case there is pre-existing DB setup from prior runs
db.drop_all()

# Creating DB 
db.create_all()

# 3 forms with each function for processing (register & login & spellinput)
@app.route('/')
def index():
    return "Welcome to Joe Gumke JDG597 - Spell Checker Web Application!!!"

# Form for register 
@app.route('/register', methods=['POST','GET'])
def register():
    registrationform = RegistrationForm(request.form)
    if request.method == 'POST' and registrationform.validate():
        uname = (registrationform.uname.data)
        pword = (registrationform.pword.data)
        mfa = (registrationform.mfa.data)
        try: 
            dbUserCheck = userTable.query.filter_by(username=('%s' % uname)).first()
        except AttributeError:
            userToAdd = userTable(username=uname, password=pword ,multiFactor=mfa)
            db.session.add(userToAdd)
            db.session.commit()
            print('User Successfully Registered')
            error="success"
            return render_template('register.html', form=registrationform, error=error)
        try:
            if uname == dbUserCheck.username:
                print('User Already Exists')
                error='failure'
                return render_template('register.html', form=registrationform, error=error)
        except AttributeError:
                userToAdd = userTable(username=uname, password=pword ,multiFactor=mfa)
                db.session.add(userToAdd)
                db.session.commit()
                print('User Successfully Registered')
                error="success"
                return render_template('register.html', form=registrationform, error=error)

    else:
        error=''
        return render_template('register.html', form=registrationform, error=error)

# Form for login
@app.route('/login', methods=['POST','GET'])
def login():
    loginform = RegistrationForm(request.form)

    if request.method == 'POST' and loginform.validate() and not session.get('logged_in'): 
        uname = (loginform.uname.data)
        pword = (loginform.pword.data)
        mfa = (loginform.mfa.data)
        try:
            dbUserCheck = userTable.query.filter_by(username=('%s' % uname)).first()
            
            if uname == dbUserCheck.username and pword == dbUserCheck.password and mfa == dbUserCheck.multiFactor:
                session['logged_in'] = True
                error="Successful Authentication"
                return render_template('login.html', form=loginform,error=error)

            if uname != dbUserCheck.username or pword != dbUserCheck.password:
                error='Incorrect'
                return render_template('login.html', form=loginform,error=error)
            if mfa != dbUserCheck.multiFactor:
                error='Two-Factor'
                return render_template('login.html', form=loginform,error=error)  
        except AttributeError:
            error='Incorrect'
            return render_template('login.html', form=loginform,error=error)

    else:
        error=''
        return render_template('login.html', form=loginform,error=error)


@app.route('/home', methods=['POST','GET'])
def home():
    if session.get('logged_in') and request.method =='GET':
        error = 'Authenticated User '
        return render_template('home.html', error=error)
    
    if session.get('logged_in') and request.method =='POST' and request.form['submit_button'] =='Log Out':
        error='Logged Out'
        session.pop('logged_in', None)
        return render_template('home.html', error=error)

    if session.get('logged_in') and request.method =='POST' and request.form['submit_button'] =='Spell Checker':
        error='Successful Request to Spell Checker'
        return render_template('home.html', error=error)

    else:
        error='Please Login'
        return render_template('home.html', error=error)

# Text Submission && Result Retrieval 
@app.route('/spell_check', methods=['POST','GET'])
def spell_check():
    form = wordForm(request.form)
    misspelled =[]

    if session.get('logged_in') and request.method == 'GET':
        error='inputtext'
        return render_template('spell_check.html', form=form, error=error)

    if session.get('logged_in') and request.method == 'POST' and request.form['submit_button'] == 'Check Spelling':
        data = (form.textbox.data)
        tempFile = open("temp.txt","w")
        tempFile.write(data)
        tempFile.close()
        testsub = subprocess.Popen(["./a.out", "temp.txt", "wordlist.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = testsub.stdout.read().strip()
        testsub.terminate()
        for line in output.decode('utf-8').split('\n'):
            misspelled.append(line.strip())
        return render_template('results.html', misspelled=misspelled)
        #except:
        #    return "errors"
        #return render_template('spell_check.html', form=form)

    if not session.get('logged_in'):
        error='Login Before Accessing Spell Checker'
        return render_template('spell_check.html', form=form,error=error)

    else:
        error='spellCheck else statement'
        return render_template('spell_check.html', form=form, error=error)

if __name__ == '__main__':
    app.run(debug=True)
	
