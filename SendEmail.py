import smtplib
from email.mime.text import MIMEText

class SendEmail():     
    def __init__(self):
        self.mailto_list = ['zhihzhou@cn.ibm.com', 'wujz@cn.ibm.com', 'wluxu@cn.ibm.com'] 
        self.mail_host="9.30.199.60"
        self.mail_port=25
        self.mail_user="automation_test_result"
        self.mail_postfix="noreply.ibm.com"
    
    def sendEmail(self,build_index,subject,test_summary_content,status):
        sender = "<"+self.mail_user+'@'+self.mail_user+">"
        msg = MIMEText(test_summary_content,_subtype='plain')
        msg['Subject'] = subject+" "+status
        msg['From'] = sender
        msg['To'] = ";".join(self.mailto_list)
        try:
            server = smtplib.SMTP()
            server.connect(self.mail_host,self.mail_port)
            server.sendmail(sender,self.mailto_list,msg.as_string())
            server.close()
            return True
        except Exception, e:
            print(str(e))
            return False
