import flask
#from flask_oauth import OAuth
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
import binascii,hashlib
import subprocess
import json
from OpenSSL import SSL
import requests, urllib
import threading, time
from requests.auth import HTTPBasicAuth
context = ('companyA.crt','companyA.key')

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

stored_val = json.load(open("storage.json"))
seeker_company_url = ""

dev_auth=dict()

def tmp(a,b):
    print(a)
    print(b)
    if(len(b)<10):
        b=b+b
        t=threading.Timer(2,tmp,[a,b])
        t.start()
        t.join()

def retryTokenRetrieval(username,password,trans_id,id):
    global dev_auth
    data={"trans_id":trans_id,"id":id}
    response = requests.post('https://'+seeker_company_url+'/getAuthToken',auth=HTTPBasicAuth(username,password),data=data,verify='../companyB.crt')
    if(response.status_code==200):
        authToken=response.test
        dev_auth[id]=authToken
    else:
        t=threading.Timer(10, retryTokenRetrieval,[username,password,trans_id,id])
        t.start()
        t.join()

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    username="dhjzbcbb"
    password="2020-05-15 01:49:56.640703"
    data={"trans_id":1,"id":1}
    response = requests.post('https://'+"localhost:9021"+'/getAuthToken',auth=HTTPBasicAuth(username,password),data=data,verify='../companyB.crt')
    print(str(response.status_code)+":"+response.text)
    '''
    uname=(flask.request.authorization['username'])
    pword=(flask.request.authorization['password'])
    try:
        connection = mysql.connector.connect(host='127.0.0.1',
                                             port=3306,
                                             database='objshare',
                                             user='root',
                                             password='')

        cursor = connection.cursor()
        pword=hashlib.sha256(pword.encode('ascii')).hexdigest()
        sql_select_blob_query = "INSERT INTO USERS VALUES('"+uname+"','"+pword+"')"

        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        connection.close()
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    '''
    return "hello"

#talk to companyB for the auth token
@app.route('/requestAuthToken', methods=['POST'])
@cross_origin()
def requestAuthToken():
    global stored_val
    global seeker_company_url
    id=flask.request.form['id']
    seeking=flask.request.form['seeking']
    price=flask.request.form['price']
    user=flask.request.form['user']
    tid=flask.request.form['tid']
    tmp=[id,seeking,price,user,tid]
    if((None in tmp) or ("" in tmp)):
        return "enough args not provided"
    try:
        connection = mysql.connector.connect(host='127.0.0.1',
                                             port=3306,
                                             database='objshare',
                                             user='root',
                                             password='')

        cursor = connection.cursor()
        #get company url of device from id if company exists
        sql_select_blob_query = "SELECT url FROM company where cname in (SELECT company FROM device_company WHERE dev_id='"+id+"')"

        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        result=cursor.fetchall()
        seeker_company_url=""
        if(len(result)==0):
            connection.close()
            return "no such id exists"
        else:
            seeker_company_url=result[0][0]
        connection.close()
        #data=[("id",id),("user",user),("seeking",seeking),("price",price)]
        data={"id":id,"user":user,"seeking":seeking,"price":price,"tid":tid}
        response = requests.post('https://'+seeker_company_url+'/genAuthToken',data=data,verify='../companyB.crt')
        if(response.status_code==200):
            #print(response.test+" to generate OAuth request")
            resp=json.loads(response.text)
            print(resp)
            #retryTokenRetrieval(resp["username"],resp["password"],resp["trans_id"],id)
            r=dict()
            r["username"]=resp["username"]
            r["password"]=resp["password"]
            r["trans_id"]=resp["trans_id"]
            r["id"]=id
            return r,200
        else:
            print(response.status_code)
            print(response.text)
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    print("request authToken failed")
    return "failed",400

#get auth token from companyB
@app.route('/getAuthTokenFromCompany', methods=['POST'])
@cross_origin()
def getAuthToken():
    global seeker_company_url
    id=flask.request.form['id']
    trans_id=flask.request.form['trans_id']
    username=flask.request.form['username']
    password=flask.request.form['password']
    tmp=(id,trans_id,username,password)
    if((None in tmp) or ("" in tmp)):
        return "too few arguemnets",400
    global dev_auth
    data={"trans_id":trans_id,"id":id}
    response = requests.post('https://'+seeker_company_url+'/getAuthToken',auth=HTTPBasicAuth(username,password),data=data,verify='../companyB.crt')
    if(response.status_code==200):
        authToken=response.text
        dev_auth[id]=authToken
        return authToken,200
    return "failed",404
    

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9020,ssl_context=context)
