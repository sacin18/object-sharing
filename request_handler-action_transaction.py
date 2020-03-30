# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 15:07:05 2020

@author: sacin
"""

from flask import Flask,request,jsonify,abort
from flask_cors import CORS, cross_origin  
import datetime
import subprocess
import ast
import requests as req
import json

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def transfer_packed(from_account,to_account,quantity,memo):
    splitter=['cleos','push','action','eosio.token','transfer','{"from":"'+from_account+'","to":"'+to_account+'","quantity":"'+quantity+'","memo":"'+memo+'"}','-p',from_account+'@active','-d','-j','--return-packed']
    process = subprocess.Popen(splitter,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr=process.communicate()
    t=dict()
    if stdout.decode('ascii')=="":
        t["stdout"]=stdout.decode('ascii').replace("\n","").replace("\"",'"')
    else:
        t["stdout"]=ast.literal_eval(stdout.decode('ascii'))
    if stderr.decode('ascii')=="":
        t["stderr"]=stderr.decode('ascii').replace("\n","").replace("\"",'"')
    else:
        t["stderr"]=ast.literal_eval(stderr.decode('ascii'))
    return json.dumps(t)

@app.route('/exec',methods = ['GET'])
@cross_origin()
def exec_transaction():
    from_account=request.args.get('from')
    to_account=request.args.get('to')
    quantity=request.args.get('amount')
    memo=request.args.get('memo')
    if (from_account is None or to_account is None or quantity is None or memo is None):
        return abort(400)
    try:
        quantity=float(quantity)
    except:
        return abort(400)
    quantity=str(format(quantity,'.4f'))+" SYS"
    packed_trx_req=transfer_packed(from_account,to_account,quantity,memo)
    print(packed_trx_req)
    r=req.post(url="http://localhost:8888/v1/chain/push_transaction",data=json.dumps(json.loads(packed_trx_req)["stdout"]))
    return jsonify(r.json())

# main driver function 
if __name__ == '__main__': 
    app.run(host="0.0.0.0",port=9800,threaded=True)