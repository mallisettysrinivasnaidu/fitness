from flask import Flask,request,render_template,url_for,redirect,flash,session
from flask_session import Session
import mysql.connector
from dmail import sendmail
from key import secret_key,salt1,salt2
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from datetime import datetime

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE']='filesystem'
mydb = mysql.connector.connect(host='localhost',user='root',password='Admin',db='fitness_tracker')

@app.route('/')
def home():
    return render_template('title.html')

@app.route('/homepage')
def homepage():
    if session.get('user'):
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['name']
        password=request.form['password']
        email=request.form['email']
        gender=request.form['gender']
        phone=request.form['phone']
        print(request.form)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from user where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('register.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('register.html')
        data={'username':username,'password':password,'email':email,'gender':gender,'phone':phone}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt1,max_age=180)
    except Exception as e:
        print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from user where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into user values(%s,%s,%s,%s,%s)',[data['username'],data['password'],data['email'],data['gender'],data['phone']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('homepage'))
    if request.method =='POST':
        username=request.form['name']
        password=request.form['password']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('homepage'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword == confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update user set password=%s where username=%s',[newpassword,id1])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/forget',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        id1=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from user where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mysql.connection.cursor()
            cursor.execute('SELECT email  from user where username=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('reset',token=token(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


##This is Admin login Creadentials 
@app.route('/admin',methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        admin=request.form['name']
        password=request.form['password']
        if admin == 'Admin' and password == 'admin@123':
            session['admin']=password
            return redirect(url_for('viewallusers'))
        else:
            flash('Invalid username or password')
            return render_template('alogin.html')
    return render_template('alogin.html')
@app.route('/alogout')
def alogout():
    if session.get('admin'):
        session.pop('admin')
        flash('successfully log out')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('alogin'))


@app.route('/addprofile',methods=['GET','POST'])
def addprofile():
    if session.get('user'):
        if request.method=="POST":
            height=float(request.form['height'])
            weight=float(request.form['weight'])
            age=int(request.form['age'])
            cursor=mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO profiles (full_name, height, weight, age) VALUES (%s, %s, %s, %s)',[session['user'],height,weight,age])
            mydb.commit()
            mydb.close()
            flash('profile added sucessfully')
            return redirect(url_for('viewprofile'))
        return render_template('addprofile.html')
    return redirect(url_for('login'))
@app.route('/viewprofile',methods=['GET','POST'])
def viewprofile():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from profiles where full_name=%s',[session['user']])
        data= cursor.fetchall()
        return render_template('viewprofile.html',d=data)
    return redirect(url_for('login'))
@app.route('/update_profile',methods=['GET','POST'])
def update_profile():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from profiles where full_name = %s',[session['user']])
        data = cursor.fetchall()
        if request.method=="POST":
            height=float(request.form['height'])
            weight=float(request.form['weight'])
            age=int(request.form['age'])
            
            cursor=mydb.cursor(buffered=True)
            cursor.execute("UPDATE profiles SET height = %s, weight = %s, age = %s WHERE full_name = %s",[height,weight,age,session['user']])
            mydb.commit()
            flash('updated sucessfully')
            return redirect(url_for('viewprofile'))
        return render_template('update_profile.html',d = data)
    return redirect(url_for('login'))
@app.route('/addexercise',methods=['GET','POST'])
def addexercise():
    if session.get('user'):
        if request.method=="POST":

            exercises = request.form.getlist('exercises[]')
            durations = request.form.getlist('durations[]')
            l=[]
            for i in durations:
                if i=='':
                    i=0
                    l+=[i]
                else:
                    l+=[i]
            print(l)            
            weight = float(request.form.get('weight')) # Convert weight to float
            check_in_time = request.form.get('check_in_time')

            total_duration_minutes = sum(map(int, l))

            # Calculate calories burned per minute based on weight (example formula)
            calories_per_minute = weight * 0.1  # Example formula, adjust as needed

            # Calculate total calories burned
            total_calories_burned = total_duration_minutes * len(exercises) * calories_per_minute
            weight_after_calories = weight - (total_calories_burned / 7700)  # Assuming 7700 calories burn 1 kg
            log_date = datetime.now().date()
            # Calculate weight after calories burned
            cursor=mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO exercise_logs (user_id, total_duration_minutes, check_in_time, weight_kg, calories_burned, log_date) VALUES (%s, %s, %s, %s, %s, %s)',
                           (session['user'], total_duration_minutes, check_in_time, weight_after_calories, total_calories_burned, log_date))

            
            flash(f'Total duration: {total_duration_minutes} minutes.', 'info')
            flash(f'Total calories burned: {total_calories_burned} calories.', 'info')
            flash(f'User weight before exercise: {weight} kg.', 'info')
            flash(f'User weight after exercise: {weight_after_calories} kg.', 'info')
            mydb.commit()
            flash('data inserted sucessfully')
            return redirect(url_for('viewexerciselog'))

        return render_template('addexerciselog.html')
    return redirect(url_for('login'))
@app.route('/viewexerciselog')
def viewexerciselog():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from exercise_logs where user_id=%s',[session['user']])
        data=cursor.fetchall()

        return render_template('viewexerciselog.html',d=data)
    return redirect(url_for('login'))
@app.route('/viewallusers')
def viewallusers():
    if session.get('admin'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from exercise_logs')
        data = cursor.fetchall()

        return render_template('viewallusers.html',d=data)
    return redirect(url_for('login'))

from flask import session

@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    if session.get('user'):
        if request.method == 'POST':
            user_id = session.get('user')
            print("User ID from session:", user_id)  # Debugging: Print the user ID
            
            goal_type = request.form['goal_type']
            target_value = float(request.form['target_value'])
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO goals (user_id, goal_type, target_value, start_date, end_date) VALUES (%s, %s, %s, %s, %s)',
                           (user_id, goal_type, target_value, start_date, end_date))
            mydb.commit()
            flash('Goal set successfully')
            return redirect(url_for('homepage'))
        return render_template('set_goal.html')
    return redirect(url_for('login'))




# Add this part in your code where you initialize the database connection
# Define a function to create the goals table if it doesn't exist
def create_goals_table():
    cursor = mydb.cursor(buffered=True)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            goal_type VARCHAR(50),
            target_value FLOAT,
            start_date DATE,
            end_date DATE,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    """)
    mydb.commit()
    cursor.close()

# Call the function to create the table when the application starts
create_goals_table()

import plotly.graph_objs as go

class DataAnalysis:
    @staticmethod
    def calculate_average_weight(user_id):
        # Example: Query database to get user's weight data
        weights = [70, 72, 71, 73, 75]  # Example weights
        if weights:
            average_weight = sum(weights) / len(weights)
            return average_weight
        else:
            return None

@app.route('/weight_trend_report')
def weight_trend_report():
    if session.get('user'):
        user_id = session['user']
        average_weight = DataAnalysis.calculate_average_weight(user_id)
        if average_weight is not None:
            # Generate plot
            fig = go.Figure(data=go.Scatter(x=[], y=[]))  # Example plot
            fig.update_layout(title='Weight Trend Report', xaxis_title='Date', yaxis_title='Weight (kg)')
            return render_template('report.html', plot=fig.to_html())
        else:
            return "No weight data available"  # Handle case where no weight data is available
    return redirect(url_for('login'))


if '__main__' == __name__:
    app.run(use_reloader=True,debug=True)