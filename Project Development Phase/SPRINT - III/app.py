@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense',methods=['GET', 'POST'])
def addexpense():
    print("Entering add expense")
    
    if request.method == 'POST':
        date = request.form.get('date')
        expensename = request.form.get('expensename')
        amount = request.form.get('amount')
        paymode = request.form.get('paymode')
        category = request.form.get('category')
        

        insert_sql = "INSERT INTO addexpense VALUES (?,?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)

        print("=====================================")
        
        ibm_db.bind_param(prep_stmt, 1, date)
        ibm_db.bind_param(prep_stmt, 2, expensename)
