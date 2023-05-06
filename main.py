# app.py
from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash
#from flaskext.mysql import MySQL
from flaskext.mysql import MySQL
import datetime
import pymysql
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import TruncatedSVD
#from werkzeug import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "e-commerce_website"


mysql = MySQL()
# MySQL configurations

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'admin#123'
app.config['MYSQL_DATABASE_DB'] = 'ecoomerce_ai'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor(pymysql.cursors.DictCursor)

@app.route("/")
def main():
    return render_template('home.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/error")
def error():
    return render_template('error.html')



@app.route('/addProductToCart', methods=['POST'])
def addProductToCart():
    # cursor = None
    # conn = None
    try:
        prodQuantity = int(request.form['quantity'])
        prodCode = request.form['code']
        prodName = request.form['name']
        prodPrice = float(request.form['price'])

        if request.method == 'POST' and prodCode and prodQuantity :

            allProdTotalPrice = 0
            allProdTotalQuantity = 0
            session.modified = True
            prodCartArray = {
                prodCode: {'prodName': prodName, 'prodCode': prodCode, 'prodQuantity': prodQuantity, 'prodPrice': prodPrice,
                              'totalProdPrice': prodQuantity * prodPrice}}


            if 'itemInCart' in session:
                if prodCode in session['itemInCart']:
                    for prodKey, prodValue in session['itemInCart'].items():
                        if prodCode == prodKey:
                            oldProdQantity = session['itemInCart'][prodKey]['prodQuantity']
                            totalProdQuantity = oldProdQantity + prodQuantity
                            session['itemInCart'][prodKey]['prodQuantity'] = totalProdQuantity
                            session['itemInCart'][prodKey]['totalProdPrice'] = totalProdQuantity * prodPrice
                else:
                    session['itemInCart'] = array_merge(session['itemInCart'], prodCartArray)

                for prodKey, prodValue in session['itemInCart'].items():
                    individualProdQuantity = int(session['itemInCart'][prodKey]['prodQuantity'])
                    individualProdPrice = float(session['itemInCart'][prodKey]['totalProdPrice'])
                    allProdTotalQuantity = allProdTotalQuantity + individualProdQuantity
                    allProdTotalPrice = allProdTotalPrice + individualProdPrice
            else:
                session['itemInCart'] = prodCartArray
                allProdTotalQuantity = allProdTotalQuantity + prodQuantity
                allProdTotalPrice = allProdTotalPrice + prodQuantity * prodPrice

            session['allProdTotalQuantity'] = allProdTotalQuantity
            session['allProdTotalPrice'] = allProdTotalPrice

            session.modified = True
            session['addCall'] = 1
            return redirect(url_for('.getProducts'))
        else:
            return 'Error while adding item to cart'
    except Exception as e:
        print(e)
    # finally:
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()
    return 'Error while adding item to cart'



@app.route('/checkOut',methods=['GET','POST'])
def checkOut():

    # print(session)

    userId = session['userId']

    codeKeys = [key for key in session['itemInCart'].keys() if session['itemInCart'][key].get('prodCode') is not None]

    productIds = codeKeys
    print("checkout : ", userId," : ", productIds)

    for productCode in productIds:

        proname = session["itemInCart"][productCode]["prodName"]

        now = datetime.datetime.now()
        query = "INSERT INTO shoppingHistory (user_id, pid, prodname, created) VALUES (%s, %s, %s, %s)"
        values = (userId, productCode,proname, now)
        cursor.execute(query, values)

        print(cursor.rowcount, "record inserted.")

    if cursor.rowcount > 0:
        conn.commit()
        print('checkout success !')
        session.modified = True
        session.clear()
        session['userId'] = userId
        session['addCall'] = 0
        return redirect(url_for('getProducts'))
    else:
        return 'error'



@app.route('/postSignup',methods=['GET','POST'])
def postSignup():


    userName = request.form['inputName']
    userEmail = request.form['inputEmail']
    userPassword = request.form['inputPassword']
    print(userName,userEmail, userPassword)

    cursor.callproc('sp_createUser',(userName,userEmail, userPassword))
    data = cursor.fetchall()
    print(data)
    if len(data) == 0:
        conn.commit()
        print('User created successfully !')
        flash('User created successfully !')
        # return json.dumps({'message': 'User created successfully !'})
        return render_template('login.html')
    else:
        dataKey = list(data[0].keys())[0]
        error_message = f'An error occurred: {dataKey}'
        print(error_message)
        flash(error_message)
        return render_template('signup.html')



@app.route('/postLogin', methods=['POST'])
def postLogin():

    # read the posted values from the UI
    # _name = request.form['inputName']
    try:
        userEmail = request.form['inputEmail']
        userPassword = request.form['inputPassword']
        print(userEmail, userPassword)

        cursor.execute("SELECT * FROM usergrp WHERE user_username = %s and user_password = %s ", (userEmail,userPassword))
        data = cursor.fetchall()

        if len(data) > 0:
            # conn.commit()
            session.clear()
            session.modified = True
            session['userId'] = userEmail
            session['addCall'] = 0
            return redirect(url_for('getProducts'))
        else:
            return 'error login'

    except Exception as e:
        print(e)

    return 'Error post login end'


myProdList = []

@app.route('/getProducts')
def getProducts():
    # cursor = None
    # conn = None
    try:
        userId = session['userId']
        # conn = mysql.connect()
        # cursor = conn.cursor(pymysql.cursors.DictCursor)
        if session['addCall'] == 0:
            global myProdList
            myProdList =[]
            prodRatings = pd.read_csv('ratings_Beauty.csv')
            prodRatings = prodRatings.dropna()
            prodRatingsFilter = prodRatings.head(10000)
            ratingsUtilityMatrix = prodRatingsFilter.pivot_table(values='Rating', index='UserId', columns='ProductId',
                                                                 fill_value=0)
            xtrans = ratingsUtilityMatrix.T

            singularValueDecomposition = TruncatedSVD(n_components=10)
            decomposedMatrix = singularValueDecomposition.fit_transform(xtrans)

            correlationMatrix = np.corrcoef(decomposedMatrix)

            #raj add userid basis get latest bought product, find index in dataframe

            cursor.execute("SELECT pid FROM shoppingHistory WHERE user_id = %s  order by created desc LIMIT 1",
                           (userId))
            data = cursor.fetchone()
            if len(data) >0:
                i = data['pid']
            else:
                i = xtrans.index[99]

            productNames = list(xtrans.index)
            productID = productNames.index(i)
            correlationProductID = correlationMatrix[productID]

            Recommend = list(xtrans.index[correlationProductID > 0.90])

            # Removes the item already bought by the customer
            Recommend.remove(i)

            print(Recommend[0:9])

            for item in Recommend[0:9]:

                myDict = {}
                myDict['code'] = item
                # myDict['name'] = amazon_ratings.loc[amazon_ratings['ProductId'] == item, 'ProdName'].values[0]
                myDict['name'] = item
                myDict['price'] = prodRatings.loc[prodRatings['ProductId'] == item, 'Price'].values[0]

                myProdList.append(myDict)

        return render_template('product.html', productsList=myProdList)
    except Exception as e:
        print(e)
    # finally:
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()
    return "Error occurred while retrieving products"


@app.route("/logout")
def logout():
    session.clear()
    return render_template('login.html')

@app.route('/empty')
def empty_cart():
    try:
        userId= session['userId']
        session.clear()
        session.modified = True
        session['userId'] = userId
        session['addCall'] = 1
        return redirect(url_for('.getProducts'))
    except Exception as e:
        print(e)
    return "Error occurred while retrieving"



@app.route('/delete/<string:code>')
def deleteProductFromCart(code):
    try:
        allProdTotalPrice = 0
        allProdTotalQuantity = 0
        session.modified = True
        print("deleteProductFromCart")
        for item in session['itemInCart'].items():
            if item[0] == code:
                session['itemInCart'].pop(item[0], None)
                if 'itemInCart' in session:
                    for key, value in session['itemInCart'].items():
                        individualProdQuantity = int(session['itemInCart'][key]['prodQuantity'])
                        individualProdPrice = float(session['itemInCart'][key]['totalProdPrice'])
                        allProdTotalQuantity = allProdTotalQuantity + individualProdQuantity
                        allProdTotalPrice = allProdTotalPrice + individualProdPrice
                break

        if allProdTotalQuantity == 0:
            userId = session['userId']
            session.clear()
            session.modified = True
            session['userId'] = userId
            session['addCall'] = 1
        else:
            session['allProdTotalQuantity'] = allProdTotalQuantity
            session['allProdTotalPrice'] = allProdTotalPrice

        return redirect(url_for('.getProducts'))
    except Exception as e:
        print(e)
    return "Error occurred while deleting"


def array_merge(first_array, second_array):
    if isinstance(first_array, list) and isinstance(second_array, list):
        return first_array + second_array
    elif isinstance(first_array, dict) and isinstance(second_array, dict):
        return dict(list(first_array.items()) + list(second_array.items()))
    elif isinstance(first_array, set) and isinstance(second_array, set):
        return first_array.union(second_array)
    return False


if __name__ == '__main__':
    app.run(debug=True)