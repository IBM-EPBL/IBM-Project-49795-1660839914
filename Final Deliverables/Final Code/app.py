import re,ibm_db
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from flask import (Flask, flash, redirect, render_template, request, session,url_for)
from flask_session import Session
from datetime import date

app = Flask(__name__)
app.debug=True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "Personal_Expense_Tracker_Application"
official_mail="expensetracker0046@gmail.com"

Session(app)


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=98538591-7217-4024-b027-8baa776ffad1.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30875;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=hhl91628;PWD=vM4lAZjxo4LsBPoJ","","")


#########################################################    HOME   ######################################################### 


@app.route("/")
def home():
    return render_template("home.html") 



#########################################################    SIGN UP   ######################################################### 



@app.route("/signup", methods=('GET', 'POST'))
def signup():
    msg=""
    if request.method == 'POST':
        name = request.form['fname']
        username =name.split(" ")[0]
        email = request.form['femail']
        mobile = request.form['mobile']
        password = request.form['password']
        
        sql = "SELECT * FROM customers WHERE email=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        
        if account:
            return render_template("already_registered.html")
        elif not re.match('[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
            return render_template('signup.html',msg=msg)
        elif not re.match(r'^[a-zA-Z0-9]+([._ ]?[a-zA-Z0-9]+)*$', name):
            msg = 'Name must contain only characters, numbers !'
            return render_template('signup.html',msg=msg)
        elif not re.match(r'^(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$', mobile):
            msg = 'Enter valid mobile number!'
            return render_template('signup.html',msg=msg)
        else:
            insert_sql = "INSERT INTO customers VALUES (?,?,?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, username)
            ibm_db.bind_param(prep_stmt, 3, email)
            ibm_db.bind_param(prep_stmt, 4, mobile)
            ibm_db.bind_param(prep_stmt, 5, password)
            ibm_db.execute(prep_stmt)
            
            message = Mail(
            from_email = official_mail,
            to_emails = email,
            subject='Registration Successful',
            html_content='<h1>Hello '+name+', <br>Welcome to Personal Expense Tracker Application (PETA) .<br>Hope we have a great journey ahead.</h1>')
            try:
                sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                sg.send(message)
            except Exception as e:
                print(e)
            
            return render_template('registration_success.html')
            
    
    return render_template('signup.html')



#########################################################    ABOUT   ######################################################### 



@app.route("/about")
def about():
    return render_template('about.html')



#########################################################    SIGN IN   ######################################################### 



@app.route("/signin" , methods=('GET', 'POST'))
def signin():
    if request.method == 'POST':
        femail = request.form['femail']
        fpassword = request.form['password']
        session["email"]=femail
        session["password"]=fpassword
        
        sql = "SELECT * FROM customers where email=? and password=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,femail)
        ibm_db.bind_param(stmt,2,fpassword)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)

        if account:
            return redirect("/dashboard")
            
        else:
            return render_template('invalid_credentials.html')
            
    return render_template('signin.html')



#########################################################    DASHBOARD   ######################################################### 



@app.route("/dashboard" , methods=('GET', 'POST'))
def dashboard():
    ml=0
    yl=0
    limit=False 
    msg=""
    months={}
    years={}
    session["date"] = date.today()
    session["date"] = str(session["date"])
    if request.method=="GET":
        query2="select * from expenses"
        exec_query=ibm_db.exec_immediate(conn,query2)
        row=ibm_db.fetch_both(exec_query)
        user=False
        while(row):
            if row[0]==session["email"]:
                if row[3][:7]==session["date"][:7]:
                    if row[3] not in months:
                        months[row[3]]=row[1]
                    else:
                        months[row[3]]+=row[1]
                if row[3][:4]==session["date"][:4]:
                    if row[3][:7] not in years:
                        years[row[3][:7]]=row[1]
                    else:
                        years[row[3][:7]]+=row[1]
            row=ibm_db.fetch_both(exec_query)
            
        query1="select * from limits"
        exec_query=ibm_db.exec_immediate(conn,query1)
        row=ibm_db.fetch_both(exec_query)
        k=False
        while(row):
            if row[0]==session["email"]:
                ml=row[1]
                yl=row[2]

            row=ibm_db.fetch_both(exec_query)
            
    session["current_month"]=[i for i in months.keys()]
    session["month_amount"]=[i for i in months.values()]
    session["current_year"]=[i for i in years.keys()]
    session["year_amount"]=[i for i in years.values()]
                                  
    if ml==0 and yl==0:
        msg="No expense limits are set, please set them to use the application"               
    if sum(session["month_amount"])>ml or sum(session["year_amount"])>yl:
        limit=True
        
    if limit==True:
        msg="Expense limit exceed Please manage your expenses."
        message = Mail(
        from_email = official_mail,
        to_emails = session["email"],
        subject='Expense Limit reached',
        html_content='<h1> Monthly expense limit reached.<br>Please use money carefully or increase budget limit.</h1>')
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        except Exception as e:
            print(e)
    
    return render_template('dashboard.html',email=session["email"],current_month=json.dumps(session["current_month"]),msg=msg,current_year=json.dumps(session["current_year"]),month_amount=json.dumps(session["month_amount"]),year_amount=json.dumps(session["year_amount"]),monthly_a=sum(session["month_amount"]),yearly_a=sum(session["year_amount"]),monthly_l=ml,yearly_l=yl)



#########################################################    PROFILE   ######################################################### 




@app.route("/profile" , methods=('GET', 'POST'))
def profile():
    sql = "SELECT * FROM customers"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while(True): 
        dictionary = ibm_db.fetch_both(stmt)
        if dictionary[2]==session["email"] and dictionary[4]==session["password"]:
            username=ibm_db.result(stmt,1) 
            name=ibm_db.result(stmt,0)
            mobile=ibm_db.result(stmt,3)  
            session["username"]=username
            break
    return render_template('profile.html',email=session["email"],username=username,mobile=mobile,name=name)



#########################################################    ADD MANUALLY   ######################################################### 



@app.route("/add_manually" , methods=('GET', 'POST'))
def add_manually():
    msg=""
    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        
        if not re.match('^[0-9]*$', amount):
            msg = 'Invalid amount !'
            return render_template('add_manually.html',msg1=msg,email=session["email"])
        else:
            insert_sql = "INSERT INTO expenses VALUES (?,?,?,?,current_date,current_time)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, session["email"])
            ibm_db.bind_param(prep_stmt, 2, amount)
            ibm_db.bind_param(prep_stmt, 3, category)
            ibm_db.bind_param(prep_stmt, 4, date)
            ibm_db.execute(prep_stmt)
            
            return render_template('add_manually.html',msg2="Added Successfully !",email=session["email"])
    
    return render_template('add_manually.html',email=session["email"])



#########################################################    ADD CSV   ######################################################### 



@app.route("/add_csv" , methods=('GET', 'POST'))
def add_csv():
    if request.method == 'POST':
        dataframe = (request.form["csv_file"])
        dataframe1 = pd.read_excel(dataframe)
        for row in dataframe1.iterrows():
            insert_sql = "INSERT INTO expenses VALUES (?,?,?,?,current_date,current_time)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, session["email"])
            ibm_db.bind_param(prep_stmt, 2, row[1][0])
            ibm_db.bind_param(prep_stmt, 3, row[1][1])
            ibm_db.bind_param(prep_stmt, 4, row[1][2])
            ibm_db.execute(prep_stmt)
        return render_template('add_csv.html',msg="Added Successfully !",email=session["email"]) 
        
    return render_template('add_csv.html',email=session["email"])



#########################################################    TABLE   ######################################################### 




@app.route("/table", methods=('GET', 'POST'))
def table():
    info=[]
    if request.method=="GET":
        query='''select * from expenses'''
        exec_query=ibm_db.exec_immediate(conn,query)
        row=ibm_db.fetch_both(exec_query)
        l=1
        while(row):
            if row[0]==session["email"]:
                info.append([l,row[0],row[1],row[2],row[3],row[4],row[5]])
                l+=1
            row=ibm_db.fetch_both(exec_query)
    return render_template('table.html',info=info,email=session["email"])



#########################################################    SET LIMIT   ######################################################### 



@app.route("/set_limit" , methods=('GET', 'POST'))
def set_limit():
    msg=""
    if request.method == 'POST':
        monthly = request.form['monthly']
        yearly = request.form['yearly']
        session["monthly"] = monthly
        session["yearly"] = yearly
        insert_sql = "INSERT INTO limits VALUES (?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, session["email"])
        ibm_db.bind_param(prep_stmt, 2, monthly)
        ibm_db.bind_param(prep_stmt, 3, yearly)
        ibm_db.execute(prep_stmt)
        return render_template('set_limit.html',msg2="Added Successfully !",email=session["email"])
        
    return render_template('set_limit.html',email=session["email"])



#########################################################    MONTHLY CHARTS   ######################################################### 



@app.route("/monthlycharts" , methods=('GET', 'POST'))
def monthlycharts():
    expenses={}
    months={}
    if request.method=="GET":
        query='''select * from expenses'''
        exec_query=ibm_db.exec_immediate(conn,query)
        row=ibm_db.fetch_both(exec_query)
        while(row):
            if row['NAME']==session["email"]:
                if row['CATOGERY'] not in expenses:
                    expenses[row['CATOGERY']]=row['AMOUNT']
                else:
                    expenses[row['CATOGERY']]+=row['AMOUNT']
                    
                dates=row['BILL_TIME'][:7]
                amount=row['AMOUNT']
                if dates not in months:
                    months[dates]=amount
                else:
                    months[dates]+=amount

            row=ibm_db.fetch_both(exec_query)
        session["piecategories"]=[i for i in expenses.keys()]
        session["pieamount"]=[i for i in expenses.values()]
        session["barcategories"]=[i for i in months.keys()]
        session["baramount"]=[i for i in months.values()]
            
        return render_template('monthlycharts.html',email=session["email"],piecategories=json.dumps(session["piecategories"]),pieamount=json.dumps(session["pieamount"]),barcategories=json.dumps(session["barcategories"]),baramount=json.dumps(session["baramount"]),length=json.dumps(len(session["barcategories"])),s=sum(session["baramount"]))

        
    return render_template('monthlycharts.html',email=session["email"])



#########################################################    YEARLY CHARTS   ######################################################### 



@app.route("/yearlycharts" , methods=('GET', 'POST'))
def yearlycharts():
    expenses={}
    yearly={}
    if request.method=="GET":
        query='''select * from expenses'''
        exec_query=ibm_db.exec_immediate(conn,query)
        row=ibm_db.fetch_both(exec_query)
        while(row):
            if row['NAME']==session["email"]:
                if row['CATOGERY'] not in expenses:
                    expenses[row['CATOGERY']]=row['AMOUNT']
                else:
                    expenses[row['CATOGERY']]+=row['AMOUNT']
                    
                dates=row['BILL_TIME'][:4]
                amount=row['AMOUNT']
                if dates not in yearly:
                    yearly[dates]=amount
                else:
                    yearly[dates]+=amount

            row=ibm_db.fetch_both(exec_query)
        session["piecategories"]=[i for i in expenses.keys()]
        session["pieamount"]=[i for i in expenses.values()]
        session["yearbarcategories"]=[i for i in yearly.keys()]
        session["yearbaramount"]=[i for i in yearly.values()]
            
        return render_template('yearlycharts.html',email=session["email"],piecategories=json.dumps(session["piecategories"]),pieamount=json.dumps(session["pieamount"]),barcategories=json.dumps(session["yearbarcategories"]),baramount=json.dumps(session["yearbaramount"]),length=json.dumps(len(session["yearbarcategories"])),s=sum(session["pieamount"]))

        
    return render_template('yearlycharts.html',email=session["email"])



#########################################################    LOG OUT   ######################################################### 



@app.route("/logout")
def logout():
    session.pop("email",default=None)
    session.pop("password",default=None)
    session.pop("username",default=None)
    session.pop("monthly",default=None)
    session.pop("yearly",default=None)
    session.pop("piecategories",default=None)
    session.pop("pieamount",default=None)
    session.pop("barcategories",default=None)
    session.pop("baramount",default=None)
    session.pop("yearbarcategories",default=None)
    session.pop("yearbaramount",default=None)
    return redirect("/login")


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)