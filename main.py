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

    # read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
    print(_name,_email, _password)

    cursor.callproc('sp_createUser',(_name,_email, _password))
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
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']
        print(_email, _password)

        cursor.execute("SELECT * FROM usergrp WHERE user_username = %s and user_password = %s ", (_email,_password))
        data = cursor.fetchall()

        if len(data) > 0:
            # conn.commit()
            session.clear()
            session.modified = True
            session['userId'] = _email
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
        # conn = mysql.connect()
        # cursor = conn.cursor(pymysql.cursors.DictCursor)
        if session['addCall'] == 0:
            global myProdList
            myProdList =[]
            amazon_ratings = pd.read_csv('ratings_Beauty.csv')
            amazon_ratings = amazon_ratings.dropna()
            amazon_ratings1 = amazon_ratings.head(10000)
            ratings_utility_matrix = amazon_ratings1.pivot_table(values='Rating', index='UserId', columns='ProductId',
                                                                 fill_value=0)
            ratings_utility_matrix.shape
            X = ratings_utility_matrix.T
            X.shape
            X1 = X
            SVD = TruncatedSVD(n_components=10)
            decomposed_matrix = SVD.fit_transform(X)
            decomposed_matrix.shape
            correlation_matrix = np.corrcoef(decomposed_matrix)
            correlation_matrix.shape
            #raj add userid basis get latest bought product, find index in dataframe


            i = X.index[99]

            product_names = list(X.index)
            product_ID = product_names.index(i)
            correlation_product_ID = correlation_matrix[product_ID]
            correlation_product_ID.shape
            Recommend = list(X.index[correlation_product_ID > 0.90])

            # Removes the item already bought by the customer
            Recommend.remove(i)

            print(Recommend[0:9])

            for item in Recommend[0:9]:

                my_dict = {}
                my_dict['code'] = item
                # my_dict['name'] = amazon_ratings.loc[amazon_ratings['ProductId'] == item, 'ProdName'].values[0]
                my_dict['name'] = item
                my_dict['price'] =  amazon_ratings.loc[amazon_ratings['ProductId'] == item, 'Price'].values[0]

                myProdList.append(my_dict)

    #
            # cursor.execute("SELECT * FROM product")
            # rows = cursor.fetchall()
            # print(rows)
        return render_template('product.html', productsList=myProdList)
    except Exception as e:
        print(e)
    # finally:
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()
    return "Error occurred while retrieving products"




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