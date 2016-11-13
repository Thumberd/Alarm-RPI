#Import lib
try:
    import MySQLhandler
except ImportError:
    print("Error: Unable to import MySQLhandler")
    exit

class Mail:
    ######################################################################
    #                                                                    #
    # @__init__                                                          #
    # Usage                                                              #
    # mail = Mail('to@mail.com', 'The subject', 'The message')           #
    #                                                                    #
    ######################################################################
    def __init__(self, toaddr = None,subject = None, message = None):
        self.toaddr = toaddr
        self.subject = subject
        self.message = message

        #Import smtplib
        try:
            import smtplib
        except ImportError:
            print("Error: Unable to import smtplib")
            exit

        #Open file containing credentials
        try:
            with open('mailCredential.txt', 'r') as f:
                self.credentials = f.read().split('*')
        except FileNotFoundError:
            print("Unable to get credentials: mailCredential.txt not found")

        #Create connection
        try:
            self.server = smtplib.SMTP(self.credentials[0])
            self.server.starttls()
            self.server.login(self.credentials[1], self.credentials[2])
        except:
            print("Unable to connect")

    ######################################################################
    #                                                                    #
    # @send                                                              #
    # Usage                                                              #
    # mail.send()                                                        #
    #                                                                    #
    ######################################################################
    def send(self):
        try:
            self.server.sendmail(self.credentials[1], self.toaddr, self.message)
        except:
            print("Unable to send mail")

    ######################################################################
    #                                                                    #
    # @all                                                               #
    # add all users email to the recipients                              #
    #                                                                    #
    ######################################################################
    def all(self):
        if 1 == 1:
            userDB = MySQLhandler.MySQL('users')
            users = userDB.all()
            self.toaddr = []
            for user in users:
                self.toaddr.append(user['email'])
            print(self.toaddr)
        else:
            print("Unable to get users mail")

class SMS:
    def __init__(self, msg):
        self.clients = None
        self.msg = msg
        try:
            import requests
            self.requests = requests
        except ImportError:
            print("Unable to import requests")

    def all(self):
        DBapifree = MySQLhandler.MySQL('apifrees')
        clients = DBapifree.all()
        for client in clients:
            r = self.requests.get('https://smsapi.free-mobile.fr/sendmsg?user=' + client['user'] + '&pass=' + client['key'] + '&msg=' + self.msg)
    def byID(self, id):
        try:
            id = int(id)
        except:
            return "Incorrect data"
        else:
            DBapifree = MySQLhandler.MySQL('apifrees')
            client = DBapifree.get('user_id', id)[0]
            if client:
                r = self.requests.get('https://smsapi.free-mobile.fr/sendmsg?user=' + client['user'] + '&pass='
                                + client['key'] + '&msg=' + self.msg)
    def to_staff(self):
        r = self.requests.get('https://smsapi.free-mobile.fr/sendmsg?user=10908880&pass=9o83gNpCCAMjjs&msg={}'
                            .format(self.msg))
