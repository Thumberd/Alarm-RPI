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
