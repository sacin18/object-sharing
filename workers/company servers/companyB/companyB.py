import flask
#from flask_oauth import OAuth
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
import binascii,hashlib
import subprocess
import json
from OpenSSL import SSL
import requests
from datetime import datetime
import random
import threading
from requests.auth import HTTPBasicAuth
from timeit import default_timer as timer
context = ('companyB.crt','companyB.key')

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

stored_val = json.load(open("storage.json"))
seeker_company_url = ""

class PaymentCheckThread(threading.Thread):
    def __init__(self, retries, invoice_id):
        threading.Thread.__init__(self)
        self.retries=retries
        self.invoice_id=invoice_id
    def run(self):
        walletUpdateChecker(self.retries,self.invoice_id)

def walletUpdateChecker(retries,invoice_id):
    if(retries<=0):
            return
    print("checking wallet update")
    response=requests.get("https://localhost:9021/updateWallet?invoice_id="+str(invoice_id),verify=False)
    if(response.status_code==200):
        print("money added to wallet successfully : "+invoice_id)
        return
    if(response.status_code!=406):
        print("payment receiver has thrown error : "+str(response.text))
        return
    t=threading.Timer(10, walletUpdateChecker,[retries-1,invoice_id])
    t.start()

def gen_random_word():
    word=[]
    for i in range(8):
        word.append(chr(random.randint(97,122)))
    return ''.join(word)

def login(username,password):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        password=hashlib.sha256(password.encode('ascii')).hexdigest()
        sql_select_blob_query = "select * from users where username='"+username+"' and password='"+password+"'"
        cursor.execute(sql_select_blob_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return False
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return True

def tmplogin(username,password):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        password=hashlib.sha256(password.encode('ascii')).hexdigest()
        sql_select_blob_query = "select * from tmp_auth where username='"+username+"' and password='"+password+"'"
        cursor.execute(sql_select_blob_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return False
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return True

def delete_tmpauth(username,password):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        password=hashlib.sha256(password.encode('ascii')).hexdigest()
        sql_select_blob_query = "delete from tmp_auth where username='"+username+"' and password='"+password+"'"
        cursor.execute(sql_select_blob_query)
        if(cursor.rowcount==0):
            connection.close()
            return False
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return True

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        sql_select_blob_query = "INSERT INTO TMP(a,t) VALUES(%s,%s)"
        cursor.execute(sql_select_blob_query,('as',None))
        connection.close()
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "hello"

#talk to companyB for the auth token
@app.route('/genAuthToken', methods=['POST'])
@cross_origin()
def genAuthToken():
    global stored_val
    global seeker_company_url
    id=flask.request.form['id']
    seeking=flask.request.form['seeking']
    price=flask.request.form['price']
    user=flask.request.form['user']
    tid=flask.request.form['tid']
    tmp=[id,seeking,price,user]
    if((None in tmp) or ("" in tmp)):
        return "enough args not provided",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        sql_select_blob_query = "insert into trans(trans_id,dev_id,tid,seeking,price,tme,authtoken) values(%s,%s,%s,%s,%s,%s,%s)"

        tme=str(datetime.fromtimestamp(datetime.timestamp(datetime.now()))).split(".")[0]
        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query,(None,id,tid,seeking,price,tme,None))
        username=gen_random_word()
        tme2=str(datetime.fromtimestamp(datetime.timestamp(datetime.now())))
        pword=hashlib.sha256(tme2.encode('ascii')).hexdigest()
        sql_select_blob_query = "insert into tmp_auth values('"+username+"','"+pword+"')"
        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        if(cursor.rowcount==0):
            connection.close()
            return "failed",400
        sql_get_trans_id_query = "select trans_id from trans where dev_id='"+id+"' and tid='"+tid+"' and tme='"+tme+"'"
        cursor.execute(sql_get_trans_id_query)
        trans_id=""
        res=cursor.fetchall()
        if(len(res)!=0):
            trans_id=res[0][0]
        connection.close()
        return {"username":username,"password":tme2,"trans_id":trans_id}
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed",400

@app.route('/getAuthorizables', methods=['GET'])
@cross_origin()
def getAuthorizables():
    global stored_val
    global seeker_company_url
    id=flask.request.args.get('id')
    if(id==None or id.strip()==""):
        return "enough args not provided",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        sql_select_blob_query = "select trans_id,tid,seeking,price,tme from trans where dev_id='"+id+"' and authtoken is null order by tme desc"
        cursor.execute(sql_select_blob_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return flask.jsonify([]),404
        else:
            out=[]
            for row in result:
                tmp=dict()
                tmp['trans_id']=row[0]
                tmp['tid']=row[1]
                tmp['seeking']=row[2]
                tmp['price']=row[3]
                tmp['tme']=row[4]
                out.append(tmp)
        connection.close()
        return flask.jsonify(out)
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return flask.jsonify([]),404

#get auth token from companyB
@app.route('/getAuthToken', methods=['POST'])
@cross_origin()
def getAuthToken():
    global stored_val
    global seeker_company_url
    if(flask.request.authorization==None):
        print("here is where the problem lies")
        return "failed",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        print("here is where the problem lies 2")
        return "failed",400
    if(not tmplogin(name,password)):
        return "failed",401
    id=flask.request.form['id']
    trans_id=flask.request.form['trans_id']
    tmp=(id,trans_id)
    if((None in tmp) or ("" in tmp)):
        print("here is where the problem lies 3")
        return "enough args not provided",400
    id=str(id)
    trans_id=str(trans_id)
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        #get company url of device from id if company exists
        sql_select_blob_query = "select authtoken from trans where dev_id='"+id+"' and trans_id='"+trans_id+"' and authtoken is not null"
        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        res=cursor.fetchall()
        if(len(res)!=0):
            delete_tmpauth(name,password)
            return res[0][0],200
        connection.close()
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed",400


@app.route('/authorize', methods=['POST'])
@cross_origin()
def authorize():
    global stored_val
    global seeker_company_url
    if(flask.request.authorization==None):
        return "failed",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "failed",400
    if(not login(name,password)):
        return "failed",401
    id=flask.request.form['id']
    trans_id=flask.request.form['trans_id']
    tmp=(id,trans_id)
    if((None in tmp) or ("" in tmp)):
        return "enough args not provided"
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])

        cursor = connection.cursor()
        tme=str(datetime.fromtimestamp(datetime.timestamp(datetime.now())))
        authToken=str(hashlib.sha256(tme.encode('ascii')).hexdigest())
        #get company url of device from id if company exists
        sql_select_blob_query = "select authtoken from trans where dev_id='"+id+"' and trans_id='"+trans_id+"' and authtoken is not null"
        sql_update_blob_query = "update trans set tme='"+tme+"',authtoken='"+authToken+"' where dev_id='"+id+"' and trans_id='"+trans_id+"' and authtoken is null"
        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        res=cursor.fetchall()
        if(len(res)!=0):
            return res[0][0],200
        cursor.execute(sql_update_blob_query)
        val=cursor.rowcount
        if(val==0):
            return "failed",404
        connection.close()
        return authToken
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed",400

@app.route('/verifyAuth', methods=['POST'])
@cross_origin()
def verifyAuth():
    auth=flask.request.form['authToken']
    print(auth)
    return "successful",200

@app.route('/addWalletMoney', methods=['GET'])
@cross_origin()
def addWalletMoney():
    print("addWalletMoney")
    money=flask.request.args.get("money")
    user=flask.request.args.get("user")
    tmp=[user,money]
    if((None in tmp) or ("" in tmp)):
        return "enough arguements not passed",400
    try:
        money=float(money)
    except:
        return "float values expected for money",400
    money=money*100
    username=stored_val['razorpay_user']
    password=stored_val['razorpay_password']
    data=dict()
    data["amount"]=int(money)
    data["type"]= "link"
    data["description"]="adding wallet money to account : "+str(user)
    data["customer"]=dict()
    data["customer"]["name"]=str(user)
    response = requests.post('https://api.razorpay.com/v1/invoices',
        auth=HTTPBasicAuth(username,password),json=data,verify=False)
    if(response.status_code==200):
        out=dict()
        resp=response.json()
        out["status"]="unpaid"
        out["link"]=resp["short_url"]
        out["inv_id"]=resp["id"]
        thread1=PaymentCheckThread(10,out["inv_id"])
        thread1.start()
        return out,200
    print(response.text)
    return "request to razorpay failed",response.status_code

@app.route('/updateWallet', methods=['GET'])
@cross_origin()
def updateWallet():
    print("updateWallet")
    invoice_id=flask.request.args.get('invoice_id')
    if(invoice_id==None or invoice_id.strip()==""):
        return "invoice_id not provided",400
    username=stored_val['razorpay_user']
    password=stored_val['razorpay_password']
    response = requests.get('https://api.razorpay.com/v1/invoices/'+str(invoice_id),
        auth=HTTPBasicAuth(username,password),verify=False)
    if(response.status_code==200):
        out=dict()
        resp=response.json()
        if(resp['status']=="paid"):
            user=resp['customer_details']['name']
            try:
                connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])
                cursor=connection.cursor()
                sql_query = "select * from invoice_list where invoice_id='"+str(invoice_id)+"'"
                cursor.execute(sql_query)
                result=cursor.fetchall()
                if(len(result)==0):
                    sql_select_blob_query = "select walletname,walletpword from blockchain_wallet where username in (select username from users where username='"+user+"')"
                    cursor.execute(sql_select_blob_query)
                    result=cursor.fetchall()
                    if(len(result)==0):
                        return "error fetching user's wallet",500
                    else:
                        username=result[0][0]
                        password=result[0][1]
                        data=dict()
                        data["user"]=user
                        data["quantity"]=str(resp['amount_paid'])[:-2]+"."+str(resp['amount_paid'])[-2:]+"00 INR"
                        response=requests.post("https://localhost:9011/addBalance",
                                    auth=HTTPBasicAuth(username,password),data=data,verify='../blockchain_handler.crt')
                        if(response.status_code==200):
                            sql_query = "insert into invoice_list values('"+str(invoice_id)+"')"
                            cursor.execute(sql_query)
                            result=cursor.rowcount
                            if(result!=0):
                                connection.close()
                                return response.text,response.status_code
                        connection.close()
                        return response.text,response.status_code
                else:
                    connection.close()
                    return "invoice id already used",403
            except mysql.connector.Error as error:
                print("Failed to access mysql tables {}".format(error))
                try:
                    connection.close()
                except:
                    pass
                return "invoice id already used",403
            except requests.exceptions.ConnectionError as error:
                try:
                    connection.close()
                except:
                    pass
                return "blockchain service is not reachable",500
        else:
            return "payment due",406
    return "request to razorpay failed",response.status_code


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9021,ssl_context=context)
