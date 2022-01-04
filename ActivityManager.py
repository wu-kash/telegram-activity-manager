import datetime

class Host:

    def __init__(self, activity, time, host, msg_id):
        # Initialize here to prevent sharing with other class objects
        self.session_type = activity        # i.e. gym, tennis, etc
        self.session_time = time            # Start time
        self.session_host = host            # Who created session

        self.getTodayDate()                 # Date hosted
        
        self.session_members = []           # List of people who will join

        self.msg_id = msg_id                # Store chat and message id to modify 

    def addMember(self, user, choice):
        self.session_members.append([user, choice])

    def editMember(self, user, choice):

        for i in range(len(self.session_members)):
            if user in self.session_members[i][0]:
                self.session_members[i][1] = choice

    def cancelActivity(self, time):
        pass
    

    def getTodayDate(self):

        today_date = datetime.datetime.today()

        day = today_date.day
        month = today_date.month
        year = today_date.year

        self.session_date = f'\n{day}-{month}-{year}' 

    def storeSession(self, file):

        session_details = f'\n'
        session_details += f'{self.session_date}, {self.session_time}\n\t'
        session_details += f'{self.session_type} - [Host] {self.session_host}\n\t\t'
        session_details += f'[Members] {self.session_members}\n' 

        txt_file = open(file, "a")
        txt_file.write(session_details)
        txt_file.close()
