import json
commandFile = open('commands.json')
commands=json.load(commandFile)

class CleosCmnds:
    @staticmethod
    def wallet_list():
        return commands['wallet list']

    @staticmethod
    def wallet_unlock(name,password):
        l=commands['wallet unlock']
        l[4]=name
        l[6]=password
        return l
    
    @staticmethod
    def wallet_lock(name):
        l=commands['wallet lock']
        l[4]=name
        return l
    
    @staticmethod
    def seek_service(user,servicer,service,cost):
        l=commands['seek_service']
        l[5]="[\""+str(user)+"\",\""+str(servicer)+"\",\""+str(service)+"\",\""+str(cost)+"\"]"
        l[7]=str(user)+"@active"
        return l

    @staticmethod
    def serv_seeker(servicer,seeker,service,cost):
        l=commands['serv_seeker']
        l[5]="[\""+str(servicer)+"\",\""+str(seeker)+"\",\""+str(service)+"\",\""+str(cost)+"\"]"
        l[7]=str(servicer)+"@active"
        return l
    
    @staticmethod
    def add_service(user,service,cost):
        l=commands['add_service']
        l[5]="[\""+str(user)+"\",\""+str(service)+"\",\""+str(cost)+"\"]"
        l[7]=str(user)+"@active"
        return l

    @staticmethod
    def issue_bal(user,quantity):
        l=commands['issue_bal']
        l[5]="[\""+str(user)+"\",\""+str(quantity)+"\"]"
        l[7]=str(user)+"@active"
        return l
    
    @staticmethod
    def get_transaction(transaction_id):
        l=commands['get_transaction']
        l[3]=str(transaction_id)
        return l