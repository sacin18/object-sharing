import socket
import sys
import ssl
import threading,time
import json
import requests
import mysql.connector
from mysql.connector import Error
import hashlib
from requests.auth import HTTPBasicAuth
from timeit import default_timer as timer

host_ip = "127.0.0.1"
general_port = 9013
secure_port = 9012
stored_val = json.load(open("servicer_storage.json"))
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('./servicer.pem',"./servicer.key")
servicer_company_url = "localhost:9020"
dev_auth = dict()
blockchain_url = "localhost:9011"
misses=dict()
timeoutTimer=0
creditCut=100

def retryTokenRetrieval(username,password,trans_id,id):
    global dev_auth
    global servicer_company_url
    data={"trans_id":trans_id,"id":id,"username":username,"password":password}
    response = requests.post('https://'+servicer_company_url+'/getAuthTokenFromCompany',data=data,verify='./companyA.crt')
    if(response.status_code==200):
        authToken=response.text
        dev_auth[id]=authToken
    else:
        t=threading.Timer(10, retryTokenRetrieval,[username,password,trans_id,id])
        t.start()
        t.join()

def services_offered():
    v=input()
    if(v=="exit"):
        return "exit".encode('ascii')
    return str({"services":stored_val["services"],"id":stored_val["id"]}).encode('ascii')

def general_socket():
    global host_ip
    global general_port
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
    except socket.error as err:
        print("socket creation failed ",err)
    try:
        s.bind((host_ip,general_port))
        s.listen(5)
        while True:
            c,addr = s.accept()
            print("client addr : ",addr)
            v=services_offered()
            if(v.decode('ascii')=="exit"):
                c.close()
                break
            c.send(v)
            c.close()
    except ssl.SSLError as err:
        print("some exception ",err)


def secure_socket():
    global host_ip
    global secure_port
    global context
    global servicer_company_url
    global stored_val
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
    except socket.error as err:
        print("socket creation failed ",err)
    try:
        s.bind((host_ip,secure_port))
        s.listen(5)
        ss=context.wrap_socket(s,server_side=True)
        while True:
            c,addr = ss.accept()
            print("secure client addr : ",addr)
            val=c.recv(1024).decode('ascii')
            print(val)
            if(val!="no service required"):
                #print(val)
                val=json.loads(val.replace("'","\""))
                val["price"]=stored_val["services"][val["seeking"]]
                print("requesting company A to generate auth token from company B")
                response = requests.post('https://'+servicer_company_url+'/requestAuthToken',data=val,verify='./companyA.crt')
                if(response.status_code==200):
                    v=json.loads(response.text)
                    username=v["username"]
                    password=v["password"]
                    data={"trans_id":v["trans_id"],"id":v["id"]}
                    print("requesting company A to get auth token from company B")
                    retryTokenRetrieval(username,password,v["trans_id"],v["id"])
                    global dev_auth
                    authToken=dev_auth[v["id"]]
                    snd=dict()
                    snd["authToken"]=authToken
                    snd["id"]=stored_val["id"]
                    snd["tid"]=val["tid"]
                    snd["user"]=stored_val["user"]
                    print("here")
                    c.send(str(snd).encode('ascii'))
                    r=c.recv(1024).decode('ascii')
                    print(r)
                    if(len(r)>20):
                        connection = mysql.connector.connect(host='127.0.0.1',
                                                                port=3306,
                                                                database='objshare',
                                                                user='root',
                                                                password='')
                        cursor = connection.cursor()
                        #get company url of device from id if company exists
                        username=stored_val["user"]
                        password=stored_val["password"]
                        password=hashlib.sha256(password.encode('ascii')).hexdigest()
                        sql_select_blob_query = "select walletname,walletpword from blockchain_wallet where username in (select username from users where username='"+username+"' and password='"+password+"')"
                        cursor.execute(sql_select_blob_query)
                        result=cursor.fetchall()
                        if(len(result)==0):
                            return (False,None)
                        else:
                            username=result[0][0]
                            password=result[0][1]
                        auth=HTTPBasicAuth(username,password)
                        response = requests.post('https://'+blockchain_url+'/getTransaction',auth=auth,data={"transaction_id":r},verify='../blockchain_handler.crt')
                        if(response.status_code==200):
                            dta=json.loads(response.text.replace("'","\""))
                            if(snd["user"]==dta["from"] and dta["user"]==val["user"] and val["price"]==stored_val["services"][val["seeking"]]):
                                print("transaction 0 verified")
                                start_timer=timer()
                                c.send("verified".encode('ascii'))
                                print("performing periodic ping")
                                ping=""
                                while(ping!="close connection"):
                                    try:
                                        c.settimeout(10)
                                        ping=c.recv(1024).decode('ascii')
                                        print("seeker:"+ping)
                                        if(ping==""):
                                            print("no respose received from seeker, closing connection")
                                            break
                                    except:
                                        print("no respose received from seeker, closing connection")
                                        break
                                end_timer=timer()
                                print("time : "+str(end_timer-start_timer))
                                data=dict()
                                data["servicer"]=dta["from"]
                                data["seeker"]=dta["user"]
                                data["service"]=val["seeking"]
                                data["cost"]=str(min(int(end_timer-start_timer)*int(float(val["price"].split(" ")[0])),creditCut))+".0000 INR"
                                response = requests.post('https://'+blockchain_url+'/servSeeker',auth=auth,data=data,verify='../blockchain_handler.crt')
                                if(response.status_code==200):
                                    print("transaction completed")
                else:
                    print("company A auth token request failed")
            else:
                print("B requires no service")
            c.close()
        s.close()
    except ssl.SSLError as err:
        print("some exception ",err)

class GeneralSocketThread(threading.Thread):
    def __init__(self, threadId):
        threading.Thread.__init__(self)
        self.threadId=threadId
    def run(self):
        general_socket()

class SecureSocketThread(threading.Thread):
    def __init__(self, threadId):
        threading.Thread.__init__(self)
        self.threadId=threadId
    def run(self):
        secure_socket()

####### general socket to perform general communication 
thread1=GeneralSocketThread(1)
thread1.start()

####### secure socket used for communication hereby
secure_thread=SecureSocketThread(1)
secure_thread.start()

thread1.join()
secure_thread.join()
'''
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
except socket.error as err:
    print("socket creation failed ",err)
try:
    s.bind((host_ip,port))
    s.listen(5)
    ss=context.wrap_socket(s,server_side=True)
    while True:
        c,addr = ss.accept()
        print("client addr : ",addr)

        c.send("haha hehe".encode('ascii'))
        c.close()
    s.close()
except ssl.SSLError as err:
    print("some exception ",err)
'''