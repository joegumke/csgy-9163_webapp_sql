#app.py -- contains basics of python code. to start web service. 
#pip3 install flask-sqlalchemy
#pip3 install flask-bcrypt
#pip3 install flask-user

from flask import Flask, request, redirect,render_template, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_user, login_required
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField, IntegerField, HiddenField
from flask_wtf import CSRFProtect
import subprocess
from datetime import * 
from flask_user import roles_required,UserManager
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = '1234567891234567893242341230498120348719035192038471902873491283510981834712039847124123940812903752903847129038471290835710289675413864310867135'
csrf = CSRFProtect()
csrf.init_app(app)
bcrypt = Bcrypt(app)

# Define SQLite3 DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the SQLite Tables
class userTable(db.Model,UserMixin):
    user_id = db.Column(db.Integer(),unique=True,nullable=False,primary_key=True)
    username = db.Column(db.String(20), unique=True,nullable=False)
    password = db.Column(db.String(60),nullable=False)
    multiFactor = db.Column(db.String(11),nullable=False)
    registered_on = db.Column('registered_on', db.DateTime)
    accessRole = db.Column(db.String(50))
    def __repr__(self):
        return f"userTable('{self.user_id}','{self.username}','{self.password}','{self.multiFactor}','{self.registered_on}','{self.accessRole}')"
    def get_id(self):
        return self.user_id
    def get_active(self):
        return True

class userHistory(db.Model):
    login_id = db.Column(db.Integer(),unique=True,nullable=False,primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer(),db.ForeignKey("user_table.user_id"),unique=False)
    username = db.Column(db.String(20), unique=False,nullable=False)
    userAction = db.Column(db.String(20))
    userLoggedIn = db.Column(db.DateTime)
    userLoggedOut = db.Column(db.DateTime)

    def __repr__(self):
        return f"userHistory('{self.login_id}','{self.user_id}','{self.userAction}','{self.username}','{self.userLoggedIn}','{self.userLoggedOut}')"

class userSpellHistory(db.Model):
    queryID= db.Column(db.Integer(),unique=True,nullable=False,primary_key=True,autoincrement=True)
    username = db.Column(db.String(20), unique=False,nullable=False)
    queryText = db.Column(db.String(20000), unique=False,nullable=False)
    queryResults = db.Column(db.String(20000), unique=False,nullable=False)

    def __repr__(self):
        return f"userSpellHistory('{self.queryID}','{self.username}','{self.queryText}','{self.queryResults}')"

# Define Classes for input forms
class RegistrationForm(Form):
    uname = StringField('Username', [validators.DataRequired(message="Enter UserName"),validators.Length(min=4, max=20)])
    pword = PasswordField('Password', [validators.DataRequired(message="Enter Password"),validators.Length(min=6, max=20)])
    mfa = StringField('2FA', [validators.DataRequired(message="Enter 10 Digit Phone Number"),validators.Length(min=11,max=11,message="Enter 11 Digit Phone Number")], id='2fa')

class wordForm(Form):
    textbox = TextAreaField('textbox', [validators.DataRequired(message="Enter Words to Check"),validators.Length(max=20000)], id='inputtext')
    
class userCheckForm(Form):
    textbox = TextAreaField('textbox', [validators.DataRequired(message="Enter User To Check Audit History"),validators.Length(max=20)], id='inputtext')
    

# Purging DB in case there is pre-existing DB setup from prior runs && building new
db.drop_all()
db.create_all()


# Add in the Administrator User
adminToAdd = userTable(username='admin',password= bcrypt.generate_password_hash('Administrator@1').decode('utf-8'),multiFactor='12345678901',accessRole='admin')
db.session.add(adminToAdd)
db.session.commit()

# Initialize the user loader
@login_manager.user_loader
def user_loader(user_id):
    return userTable.query.get(user_id)

# 3 forms with each function for processing (register & login & spellinput)
@app.route('/')
def index():
    return render_template('index.html')

# Form for register 
@app.route('/register', methods=['POST','GET'])
def register():
    registrationform = RegistrationForm(request.form)
    if request.method == 'POST' and registrationform.validate():
        uname = (registrationform.uname.data)
        pword = (registrationform.pword.data)
        hashed_password = bcrypt.generate_password_hash(pword).decode('utf-8')
        mfa = (registrationform.mfa.data)
        if userTable.query.filter_by(username=('%s' % uname)).first() == None:
            userToAdd = userTable(username=uname, password=hashed_password,multiFactor=mfa,registered_on=datetime.now(),accessRole='user')
            db.session.add(userToAdd)
            db.session.commit()
            #print('User Successfully Registered')
            error="success"
            return render_template('register.html', form=registrationform, error=error)
        else:
            dbUserCheck = userTable.query.filter_by(username=('%s' % uname)).first()
            if uname == dbUserCheck.username:
                print('User Already Exists')
                error='failure'
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

        if  userTable.query.filter_by(username=('%s' % uname)).first() == None:
            error='Incorrect'
            return render_template('login.html', form=loginform,error=error)
        else :
            dbUserCheck = userTable.query.filter_by(username=('%s' % uname)).first()
            if uname == dbUserCheck.username and bcrypt.check_password_hash(dbUserCheck.password,pword) and mfa == dbUserCheck.multiFactor:
                # assign user session
                session['logged_in'] = True
                login_user(dbUserCheck)

                # establish login for user and add to userhistory table
                userLoginToAdd = userHistory(userAction='LoggedIn', username=uname,userLoggedIn=datetime.now())
                db.session.add(userLoginToAdd)
                db.session.commit()

                error="Successful Authentication"   
                return render_template('login.html', form=loginform,error=error)

            if pword != dbUserCheck.password:
                error='Incorrect'
                return render_template('login.html', form=loginform,error=error)
            if mfa != dbUserCheck.multiFactor:
                error='Two-Factor'
                return render_template('login.html', form=loginform,error=error)  

    if request.method == 'POST' and loginform.validate() and session.get('logged_in'): 
        error='Already Logged In...Please Log Out'
        return render_template('login.html', form=loginform,error=error)  

    else:
        error=''
        return render_template('login.html', form=loginform,error=error)


@app.route('/home', methods=['POST','GET'])
def home():
    # If user logged in and makes a GET request
    if session.get('logged_in') and request.method =='GET':
        error = 'Authenticated User '
        return render_template('home.html', error=error)
    # If User logged in and makes a logout request
    if session.get('logged_in') and request.method =='POST' and request.form['submit_button'] =='Log Out':
        error='Logged Out'
        session.pop('logged_in', None)
        try:
            userLogOutToAdd = userHistory(userAction='LoggedOut', username=current_user.username,userLoggedOut=datetime.now())
            db.session.add(userLogOutToAdd)
            db.session.commit()
            return render_template('home.html', error=error)
        except AttributeError:
            return render_template('unauthorized.html', error=error)

    else:
        error='Please Login'
        return render_template('unauthorized.html', error=error)
        
# Page for registered users to access their query history
@app.route('/history', methods=['GET','POST'])
def history():
    if session.get('logged_in') and request.method =='GET':
        # Wrap try / except around this statement in case there are no results (NONE)
        try:
            numqueries = userSpellHistory.query.filter_by(username=('%s' % current_user.username)).order_by(userSpellHistory.queryID.desc()).first()
            allqueries =  userSpellHistory.query.filter_by(username=('%s' % current_user.username)).all()
            numqueriesCount = numqueries.queryID
        except AttributeError:
            numqueries = ''
            numqueriesCount = 0
            allqueries = ''
        return render_template('history.html', numqueries=numqueriesCount,allqueries=allqueries)
    else:
        return render_template('unauthorized.html')

@app.route("/history/<query>")
def queryPage(query):
    if request.method == 'GET':
        try:
            query = query.replace('query','')
            history = userSpellHistory.query.filter_by(queryID=('%s' % query)).first()
            queryID = history.queryID
            submitText = history.queryText
            returnedText = history.queryResults
        except AttributeError:
            return render_template('unauthorized.html')
        return render_template('queryIDresults.html', queryID=queryID, submitText=submitText,results=returnedText)

# Page for the Admin to retrieve login history of users 
@app.route('/login_history', methods=['GET','POST'])
def login_history():
    form = userCheckForm(request.form)
    try:
        dbUserCheck = userTable.query.filter_by(username=('%s' % current_user.username)).first()

        if session.get('logged_in') and request.method =='GET' and dbUserCheck.accessRole=='admin':
            error = 'Authenticated User '
            return render_template('login_history.html', form=form, error=error)
    
        if session.get('logged_in') and request.method == 'POST' and request.form['submit_button'] == 'Check User Login History':
            userToQuery = (form.textbox.data)
            queryResults = userHistory.query.filter_by(username=('%s' % userToQuery)).all()
            return render_template('login_history_results.html', misspelled=queryResults)
        else:
            error='Please Login As Admin'
            return render_template('unauthorized.html', form=form, error=error)
    except:
        return render_template('unauthorized.html')

# Text Submission && Result Retrieval 
@app.route('/spell_check', methods=['POST','GET'])
#@login_required
def spell_check():
    form = wordForm(request.form)
    misspelled =[]
    try:
        if session.get('logged_in') and request.method == 'GET':
            error='inputtext'
            return render_template('spell_check.html', form=form, error=error)

        if session.get('logged_in') and request.method == 'POST' and request.form['submit_button'] == 'Check Spelling' :
            data = (form.textbox.data)
            tempFile = open("temp.txt","w")
            tempFile.write(data)
            tempFile.close()
            testsub = subprocess.Popen(["./a.out", "temp.txt", "wordlist.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = testsub.stdout.read().strip()
            testsub.terminate()
            # add misspelled words to userspellhistory DB
            userSpellHistoryToAdd = userSpellHistory(username=current_user.username,queryText=data,queryResults=output.decode('utf-8'))
            db.session.add(userSpellHistoryToAdd)
            db.session.commit()
            # iterate through results and return output
            for line in output.decode('utf-8').split('\n'):
                misspelled.append(line.strip())
            return render_template('results.html', misspelled=misspelled)
    except AttributeError:
        error="Please Login before accessing..." 
        return render_template('unauthorized.html', form=form, error=error)
    else:
        error='Login Before Accessing Spell Checker'
        return render_template('unauthorized.html', form=form, error=error)

if __name__ == '__main__':
    app.run(debug=True)
	
