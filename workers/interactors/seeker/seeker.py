import threading
import socket
import sys
import ssl
import json
import requests
import urllib.parse
import random
import mysql.connector
from mysql.connector import Error
import hashlib
from requests.auth import HTTPBasicAuth
import time

trusted_server_url = "https://localhost:9015"
host_ip = "127.0.0.1"
general_port = 9013
secure_port = 9012
stored_val = json.load(open("seeker_storage.json"))
cert_file = ""
servicer_host_name = "ns.server"
tid=""
services={}
seeker_company_url = "localhost:9021"
blockchain_url = "localhost:9011"

def recvHandler(rcv):
    print(rcv+" : ",end="")
    if(rcv=="haha"):
        print("ok ok")
    else:
        print("not ok")

def disconnect_emulator(c):
    time.sleep(5)
    c.send("close connection".encode("ascii"))

def blockchain_seek_service(username,password,user,servicer,service,price):
    connection = mysql.connector.connect(host='127.0.0.1',
                                            port=3306,
                                            database='objshare',
                                            user='root',
                                            password='')
    cursor = connection.cursor()
    #get company url of device from id if company exists
    password=hashlib.sha256(password.encode('ascii')).hexdigest()
    sql_select_blob_query = "select walletname,walletpword from blockchain_wallet where username in (select username from users where username='"+username+"' and password='"+password+"')"
    cursor.execute(sql_select_blob_query)
    result=cursor.fetchall()
    if(len(result)==0):
        return (False,None)
    else:
        print((result[0][0],result[0][1]))
        username=result[0][0]
        password=result[0][1]
        data={"user":user,"servicer":servicer,"service":service,"estcost":price}
        response = requests.post('https://'+blockchain_url+'/seekService',auth=HTTPBasicAuth(username,password),data=data,verify='../blockchain_handler.crt')
        if(response.status_code==200):
            print((True,response.text))
            return (True,response.text)
    return (False,None)

class SecureSocketThread(threading.Thread):
    def __init__(self, threadId):
        global servicer_host_name
        global secure_port
        global host_ip
        global stored_val
        global cert_file
        threading.Thread.__init__(self)
        self.threadId=threadId
    def run(self):
        global servicer_host_name
        global secure_port
        global host_ip
        global stored_val
        global cert_file
        global tid
        global services
        global seeker_company_url
        print("running secure thread : "+cert_file)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations("./"+cert_file)

        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        except socket.error as err:
            print("socket creation failed ",err)

        try:
            c=context.wrap_socket(s,server_hostname=servicer_host_name,server_side=False)
            c.connect((host_ip,secure_port))
            tid=random.randint(0,100000)
            print("trying to send data")
            print("service : "+stored_val["seekable"][0])
            print(services["services"].keys())
            if(stored_val["seekable"][0] in services["services"].keys()):
                c.send(str({"id":stored_val['id'],"seeking":stored_val["seekable"][0],"price":services["services"][stored_val["seekable"][0]],"user":stored_val["user"],"tid":tid}).encode('ascii'))
                rec=c.recv(1024).decode('ascii')
                print(rec)
                rec=json.loads(rec.replace("'","\""))
                data={"authToken":rec["authToken"]}
                response = requests.post('https://'+seeker_company_url+'/verifyAuth',data=data,verify='./companyB.crt')
                if(response.status_code==200):
                    print("perform blockchain seek_service")
                    seek_val=blockchain_seek_service(stored_val["user"],stored_val["password"],
                        stored_val["user"],rec["user"],stored_val["seekable"][0],
                        services["services"][stored_val["seekable"][0]])
                    if(seek_val[0]):
                        print("sending transaction id to A")
                        c.send(seek_val[1].encode('ascii'))
                        r=c.recv(1024).decode('ascii')
                        print(r)
                        #disconnect_emulator(c)
                        while(True):
                            time.sleep(5)
                            try:
                                c.send("i'm here".encode("ascii"))
                            except:
                                print("servicer connection issues")
                                break
                    else:
                        print("error!! sending transaction id to A")
            else:
                c.send("no service required".encode('ascii'))
            c.close()
        except ssl.SSLError as err:
            print("some exception ",err)

class GeneralSocketThread(threading.Thread):
    def getCertFiles(self,id):
        global host_ip
        global general_port
        global trusted_server_url
        global cert_file
        global services
        print("trying to get cert file")
        response = requests.get(trusted_server_url+'/getCertificate',params=urllib.parse.urlencode([('id',id)]),verify='../trusted_server.crt')
        if(response.status_code==200):
            resp = response.text.encode('ascii')
            #print(resp)
            if("---" in resp.decode('ascii')):
                f=open(id+"_cert.pem","wb")
                f.write(resp)
                f.close()
                cert_file=id+"_cert.pem"
                return True
        else:
            print("failed to fetch certificate file")
        return False
    def __init__(self,threadId):
        global host_ip
        global general_port
        global trusted_server_url
        global cert_file
        global services
        threading.Thread.__init__(self)
        self.threadId=threadId
    def run(self):
        global host_ip
        global general_port
        global trusted_server_url
        global cert_file
        global services
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        s.connect((host_ip,general_port))
        msg=s.recv(1024).decode('ascii')
        try:
            services=json.loads(msg.replace("'","\""))
            if(not self.getCertFiles(services['id'])):
                print("there seems to be a problem fetching the servicer's certificates. stopping communication")
            else:
                print("saving file done")
                secure_thread=SecureSocketThread(1)
                secure_thread.start()
                secure_thread.join()
        except Exception as error:
            print(error)
        s.close()

#response = requests.get(trusted_server_url+'/getCertificate',verify='../trusted_server.crt')

thread1=GeneralSocketThread(1)
thread1.start()
thread1.join()


'''
host_ip = "127.0.0.1"
port = 9013
host_name = "ns.server"
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations('./server.pem')

try:
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
except socket.error as err:
    print("socket creation failed ",err)

try:
    c=context.wrap_socket(s,server_hostname=host_name,server_side=False)#,ssl_version=ssl.PROTOCOL_TLSv1)
    c.connect((host_ip,port))
    recvHandler(c.recv(1024).decode('ascii'))
    c.close()
except ssl.SSLError as err:
    print("some exception ",err)
'''