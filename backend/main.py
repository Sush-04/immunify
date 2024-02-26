from flask import Flask ,redirect,render_template,flash
from flask_sqlalchemy import SQLAlchemy
from flask import request,url_for,session
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_required,login_manager,login_user,logout_user,LoginManager,current_user
from flask_mail import Mail
import os
import json
from email.message import EmailMessage
import ssl
import smtplib
with open('config.json','r') as c:
    params=json.load(c)["params"]

email_sender='sushmithashiva04@gmail.com'
email_password='dpbs slzr xhxe aupv'


#mydatabase connection

local_server=True
app=Flask(__name__)
app.secret_key="Sushmitha"

# app.config.update(
#     MAIL_SERVER='smtp.gmail.com',  # Replace 'your_smtp_server.net' with the SMTP server hostname for your email domain
#     MAIL_PORT=587,  # Change the port number if necessary, commonly used ports for TLS/SSL are 587 and 465
#     MAIL_USE_TLS=True,  # Use TLS encryption for secure communication
#     MAIL_USERNAME=params['gmail-user'],  # Your email address associated with the ".net" domain
#     MAIL_PASSWORD=params['gmail-password'],  # Your email account password
#     MAIL_TIMEOUT=30
# )
# mail = Mail(app)

# this is for getting the unique user access
login_manager =LoginManager(app)
login_manager.login_view='login'

# app.config['SQLALCHEMY_DATBASE_URI']='mysql://username:password@localhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/covid'
db =SQLAlchemy(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Tests(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50))


class Users(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    dob=db.Column(db.String(1000))


class Hospitaldatas(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(100),unique=True)
    name=db.Column(db.String(100))
    loc=db.Column(db.String(100))
    slot=db.Column(db.Integer)

class Bookings(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    slot=db.Column(db.Integer)
    code=db.Column(db.String(100))

@app.route("/")
def home():
    # return "<p>hello </p>"
    return render_template("index.html")



@app.route('/signup', methods=['POST','GET'])
def signup():
    
    if request.method=='POST':
        
        email=request.form.get('email')
        dob=request.form.get('dob')
        encpassword=generate_password_hash(dob)
        user= Users.query.filter_by(email=email).first()
        if user:
            print(1)
            flash("Email already exists","warning")
            return render_template("usersignup.html")
        new_user = Users(
            email=email,
            dob=encpassword,
        )
        db.session.add(new_user)
        db.session.commit()
        # new_user=db.engine.execute(f"INSERT INTO `user` (`email`,`dob`) VALUES ('{email}','{encpassword}')")
        user1= Users.query.filter_by(email=email).first()
        if user1 and check_password_hash(user1.dob,dob):
            login_user(user1)
            flash("Sign in success ","success")
            return render_template("index.html")
            # print(email,dob)

    return render_template("usersignup.html")

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form.get('email')
        dob=request.form.get('dob')
        user=Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.dob,dob):
            print(2)
            login_user(user)
            flash("Login success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")

    return render_template("userlogin.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("logout successful","warning")
    return redirect(url_for('login'))



@app.route('/admin', methods=['POST','GET'])
def admin():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        if( username==params['username'] and password==params['password']):
            session['user'] = username
            session['admin'] = True 
            flash("Login success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            
    return render_template("admin.html")


from functools import wraps
from flask import redirect, url_for, flash, session

def session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Unauthorized. Please log in.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/adminlogout')
@session_required
def adminlogout():
    print('done')
    session.pop('user', None)
    session['admin'] = False  # Set admin flag to False
    flash("Admin logout successful", "warning")
    return redirect(url_for('home'))  # Redirect to index.html


#testing whether database is connected or not



@app.route('/addhospitalinfo',methods=['POST','GET'])
def addhospitalinfo():
    hospitals = Hospitaldatas.query.all()  # Fetch all hospital data from the database
    if request.method=='POST':
        code=request.form.get('code')
        name=request.form.get('name')
        loc=request.form.get('location')
        slot=request.form.get('slot')
        code=code.upper()
        hcode=Hospitaldatas.query.filter_by(code=code).first()
        if hcode:
            flash("Hospital already exists, just update","warning")
            return render_template("hospitaldata.html", hospitals=hospitals)  # Pass hospitals data to the template
        else:
            new_hospital = Hospitaldatas(
                code=code,
                name=name,
                loc=loc,
                slot=slot,
            )
            db.session.add(new_hospital)
            db.session.commit()
            flash("Data is added successfully","info")
            # After adding new data, refresh the hospitals data
            hospitals = Hospitaldatas.query.all()
    return render_template("hospitaldata.html", hospitals=hospitals)  # Pass hospitals data to the template

@app.route('/update_hospital/<string:code>')
def update_hospital(code):
    hospital = Hospitaldatas.query.filter_by(code=code).first_or_404()
    # Render a template for updating the hospital data
    return render_template('update_hospital.html', hospital=hospital)


@app.route('/delete_hospital/<int:id>')
def delete_hospital(id):
    hospital = Hospitaldatas.query.get_or_404(id)
    db.session.delete(hospital)
    db.session.commit()
    flash('Hospital deleted successfully', 'info')
    return redirect(url_for('addhospitalinfo'))

@app.route('/updatedata', methods=['POST'])
# @login_required
def updatedata():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        location = request.form.get('location')
        slot = request.form.get('slot')

        # Retrieve the hospital record from the database based on the code
        hospital = Hospitaldatas.query.filter_by(code=code).first()

        # Update the hospital record with the new values
        hospital.name = name
        hospital.loc = location
        hospital.slot = slot

        # Commit the changes to the database
        db.session.commit()

        # Redirect back to the addhospitalinfo page
        flash("data updated","success")
        return redirect(url_for('addhospitalinfo'))
@app.route("/slot", methods=['POST', 'GET'])
@login_required
def slot():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        email_receiver=email
        slot = request.form.get('slot')
        code = request.form.get('code')
        code=code.upper()
        # Check if the provided hospital code exists in the database
        hospital = Hospitaldatas.query.filter_by(code=code).first()
        if not hospital:
            flash("Invalid hospital code. Please provide a valid code.", "danger")
            return redirect(url_for('slot'))

        # Ensure the slot requested is available
        if hospital.slot < int(slot):
            flash("Requested slot exceeds available slots for this hospital.", "danger")
            return redirect(url_for('slot'))

        # Update the available slots for the hospital
        hospital.slot -= int(slot)
        db.session.commit()

        # Book the slot for the user
        booking = Bookings(
            name=name,
            email=email,
            slot=int(slot),
            code=code,
        )
        db.session.add(booking)
        db.session.commit()
        
        subject='covid'
        body=f"""
Dear {name}\n\n We are pleased to inform you that your slot booking has been successfully confirmed.\n\nBooking details:\n\nHospiatl code:{code}\nSlots booked:{slot}\n\n\nThank you for choosing our service. If you have any further questions or need assistance, feel free to contact us
"""
        em=EmailMessage()
        em['From']=email_sender
        em['To']=email_receiver
        em['subject']=subject
        em.set_content(body)
        context=ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
            smtp.login(email_sender,email_password)
            smtp.sendmail(email_sender,email_receiver,em.as_string())

        flash("Slot booked successfully", "success")
        return redirect(url_for('slot'))

    hospitals = Hospitaldatas.query.all()
    return render_template("book.html", hospitals=hospitals)


@app.route("/test")
def test():
    # return "<p>hello </p>"
    try:
        a=Tests.query.all()
        print(a)
        return 'MY DATABASE IS CONNECTED'
    except Exception as e :
        print(e)
        return f'MY DATABASE IS NOT CONNECTED {e}'
     
if __name__ =='__main__':
    app.run()

app.run(debug=True)