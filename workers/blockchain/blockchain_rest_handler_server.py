import flask
from flask_cors import CORS, cross_origin
import subprocess
from cleosCmnds import CleosCmnds as cmd
from OpenSSL import SSL
import json
context = ('blockchain_handler.crt','blockchain_handler.key')

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    #print(flask.request.authorization['username'])
    #print(flask.request.authorization['password'])
    return "hello"

@app.route('/addBalance', methods=['POST'])
@cross_origin()
def addBalance():
    leaveUnlocked=False
    if(flask.request.authorization==None):
        return "basic authorization required",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    proc=subprocess.Popen(cmd.wallet_unlock(name,password),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if ": Already unlocked" in errors.decode('ascii'):
            leaveUnlocked=True
        else:
            return errors.decode('ascii'),400
    
    user=flask.request.form['user']
    quantity=flask.request.form['quantity']
    if(user==None or user.strip()=="" or quantity.strip()==None or quantity==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii')
        return "requires form elements servicer,seeker,service,cost! one or more parameters missing",400

    proc=subprocess.Popen(cmd.issue_bal(user,quantity),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return errors.decode('ascii'),400

    if(not leaveUnlocked):
        proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output,errors=proc.communicate()
        proc.wait()
        if(output.decode('ascii')==""):
            return errors.decode('ascii'),400
        #return output.decode('ascii')
    return "successful"

@app.route('/addService', methods=['POST'])
@cross_origin()
def addService():
    leaveUnlocked=False
    if(flask.request.authorization==None):
        return "basic authorization required",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    proc=subprocess.Popen(cmd.wallet_unlock(name,password),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if ": Already unlocked" in errors.decode('ascii'):
            leaveUnlocked=True
        else:
            return errors.decode('ascii'),400
    
    user=flask.request.form['user']
    service=flask.request.form['service']
    cost=flask.request.form['cost']
    if(user==None or user.strip()=="" or service==None or service.strip()=="" or cost.strip()==None or cost==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return "requires form elements servicer,seeker,service,cost! one or more parameters missing",400

    proc=subprocess.Popen(cmd.add_service(user,service,cost),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return errors.decode('ascii'),400

    if(not leaveUnlocked):
        proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output,errors=proc.communicate()
        proc.wait()
        if(output.decode('ascii')==""):
            return errors.decode('ascii'),400
        #return output.decode('ascii')
    return "successful"

@app.route('/seekService', methods=['POST'])
@cross_origin()
def seekService():
    transaction_id=""
    leaveUnlocked=False
    if(flask.request.authorization==None):
        return "basic authorization required",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    proc=subprocess.Popen(cmd.wallet_unlock(name,password),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if ": Already unlocked" in errors.decode('ascii'):
            leaveUnlocked=True
        else:
            print("here 1")
            return errors.decode('ascii'),400
    
    #print(cmd.seek_service(name,name,name,name))
    user=flask.request.form['user']
    servicer=flask.request.form['servicer']
    service=flask.request.form['service']
    estcost=flask.request.form['estcost']
    if(user==None or user.strip()=="" or servicer==None or servicer.strip()=="" or service==None or service.strip()=="" or estcost.strip()==None or estcost==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return "requires form elements user,servicer,service,estcost! one or more parameters missing",400

    proc=subprocess.Popen(cmd.seek_service(user,servicer,service,estcost),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    #print(proc.communicate())
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return errors.decode('ascii'),400
    else:
        transaction_id=errors.decode('ascii').split(" ")[2]

    if(not leaveUnlocked):
        proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output,errors=proc.communicate()
        proc.wait()
        if(output.decode('ascii')==""):
            return errors.decode('ascii'),400
        #return output.decode('ascii')
    return transaction_id

@app.route('/servSeeker', methods=['POST'])
@cross_origin()
def servSeeker():
    leaveUnlocked=False
    if(flask.request.authorization==None):
        return "basic authorization required",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    proc=subprocess.Popen(cmd.wallet_unlock(name,password),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if ": Already unlocked" in errors.decode('ascii'):
            leaveUnlocked=True
        else:
            return errors.decode('ascii'),400
    
    servicer=flask.request.form['servicer']
    seeker=flask.request.form['seeker']
    service=flask.request.form['service']
    cost=flask.request.form['cost']
    if(servicer==None or servicer.strip()=="" or seeker==None or seeker.strip()=="" or service==None or service.strip()=="" or cost.strip()==None or cost==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return "requires form elements servicer,seeker,service,cost! one or more parameters missing",400

    proc=subprocess.Popen(cmd.serv_seeker(servicer,seeker,service,cost),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return errors.decode('ascii'),400

    if(not leaveUnlocked):
        proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output,errors=proc.communicate()
        proc.wait()
        if(output.decode('ascii')==""):
            return errors.decode('ascii'),400
        #return output.decode('ascii')
    return "successful"

@app.route('/getTransaction', methods=['POST'])
@cross_origin()
def getTransaction():
    transaction_id=""
    transaction=""
    leaveUnlocked=False
    if(flask.request.authorization==None):
        return "basic authorization required",400
    name=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(name.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    proc=subprocess.Popen(cmd.wallet_unlock(name,password),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if ": Already unlocked" in errors.decode('ascii'):
            leaveUnlocked=True
        else:
            return errors.decode('ascii'),400
    
    #print(cmd.seek_service(name,name,name,name))
    transaction_id=flask.request.form['transaction_id']
    if(transaction_id==None or transaction_id.strip()==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return "requires form elements user,servicer,service,estcost! one or more parameters missing",400

    proc=subprocess.Popen(cmd.get_transaction(transaction_id),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output,errors=proc.communicate()
    proc.wait()
    if(output.decode('ascii')==""):
        if(not leaveUnlocked):
            proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output2,errors2=proc.communicate()
            proc.wait()
            if(output2.decode('ascii')==""):
                return errors2.decode('ascii'),400
        return errors.decode('ascii'),400
    else:
        transaction=json.loads(output.decode('ascii'))
        transaction=transaction["trx"]["trx"]["actions"][0]["data"]

    if(not leaveUnlocked):
        proc=subprocess.Popen(cmd.wallet_lock(name),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output,errors=proc.communicate()
        proc.wait()
        if(output.decode('ascii')==""):
            return errors.decode('ascii'),400
        #return output.decode('ascii')
    return str(transaction)


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9011,ssl_context=context)
