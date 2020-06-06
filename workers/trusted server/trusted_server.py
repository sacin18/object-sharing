import flask
#from flask_oauth import OAuth
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
import subprocess
from OpenSSL import SSL
context = ('trusted_server.crt','trusted_server.key')

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    return "hello"

'''
@app.route('/test-oauth',method=['GET'])
@cross_origin
def test_oauth():
    oauth=OAuth()
    tmpapp = oauth.remote_app('tmp-app',
        base_url='https://api.twitter.com/1/',
        request_token_url='https://api.twitter.com/oauth/request_token',
        access_token_url='https://api.twitter.com/oauth/access_token',
        authorize_url='https://api.twitter.com/oauth/authenticate',
        consumer_key='<your key here>',
        consumer_secret='<your secret here>'
    )
'''

@app.route('/getCertificate', methods=['GET'])
@cross_origin()
def addCertificate():
    id=flask.request.args.get('id')
    if(id==None or id.strip()==""):
        return "id not provided"
    try:
        connection = mysql.connector.connect(host='127.0.0.1',
                                             port=3306,
                                             database='objshare',
                                             user='root',
                                             password='')

        cursor = connection.cursor()
        sql_select_blob_query = "SELECT cert FROM device_cert WHERE dev_id='"+id+"'"

        #cert = convertToBinaryData("../interactors/servicer/servicer.crt")
        cursor.execute(sql_select_blob_query)
        result=cursor.fetchall()
        cert=""
        if(len(result)==0):
            connection.close()
            return "no such id exists"
        else:
            cert=result[0][0]
        #connection.commit()
        connection.close()
        return cert
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed"


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9015,ssl_context=context)
