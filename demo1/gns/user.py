class User :
    def __init__(self, name) :
        self.__name = name

    def send_email(self, event) :
        print("EMAIL: %s --- %s" % (self.__name, event))

    def send_sms(self, event) :
        print("SMS  : %s --- %s" % (self.__name, event))

