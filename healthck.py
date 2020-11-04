import socket, requests, time, threading
from mailer import send_email, build_html
from datetime import datetime

class Utils:
    MESSAGE = "TEST"
    TOKEN = ""
    UP = 1
    DOWN = 0

class Host:
    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout

class TcpHost(Host):

    def isUp(self):
        hostIsUp = False

        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.settimeout(self.timeout)
        dest = (self.host, self.port)
        
        try:
            tcp.connect(dest)
    
            tcp.send(f"auth {Utils.TOKEN}".encode('UTF-8'))
            res = tcp.recv(1024).decode('UTF-8').replace('\n','')

            if res == 'auth ok':

                tcp.send(Utils.MESSAGE.encode('UTF-8'))
                test = tcp.recv(2048).decode('UTF-8')

                if Utils.MESSAGE in test:
                    hostIsUp = True
            
            tcp.close()
        except:
            pass
        return hostIsUp

class HttpHost(Host):

    def isUp(self):
        url = f"{self.host}?auth={Utils.TOKEN}&buf={Utils.MESSAGE}"
        
        try:
            response = requests.get(url, timeout=self.timeout)
        
            if Utils.MESSAGE in response.text:
                return True
        except:
            pass
        return False

class Threshold():

    def __init__(self, health, unhealthy):
        self.health = health
        self.unhealthy = unhealthy

class HealthChecker():

    def __init__(self, host, threshold, interval, email):
        self.host = host
        self.threshold = threshold
        self.email = email
        self.interval = interval
        self.healthCount = 0
        self.unhealthyCount = 0
        self.lastStatus = Utils.UP
        self.running = None
    
    def writeLog(self, event_time, log):
        
        with open(f"log.txt", "a") as f:
            f.write(log+"\n")
    
    def calcHealth(self, status):
        event_time = datetime.now()
        if status != self.lastStatus:
            self.healthCount = 0
            self.unhealthyCount = 0
            self.lastStatus = status
        
        if status == Utils.UP:
            self.healthCount += 1
            event = "UPTIME"
        else:
            self.unhealthyCount += 1
            event = "DOWNTIME"
        
        if (status == Utils.UP and self.healthCount == self.threshold.health) or (status == Utils.DOWN and self.unhealthyCount == self.threshold.unhealthy):
            send_email(self.email, f"{event} {self.host.host}", 
                build_html(f"{event}", event_time, self))
            
            log = f"{event_time};{event};{self.host.host};{self.host.port}"
            self.writeLog(event_time, log)

            

    
    def checkHealth(self):
        self.running = True
        while(self.running):
            if self.host.isUp():
                status = Utils.UP
            else:
                status = Utils.DOWN
            
            self.calcHealth(status)
            '''print("NOW----------------")
            print(f"SERVER: {self.host.host}")
            print(f"STATUS: {status}")    
            print(f"LAST: {self.lastStatus}")
            print(f"HC: {self.healthCount}")
            print(f"UH: {self.unhealthyCount}")
            print()'''
            time.sleep(self.interval)

class CloudWalkHealthChecker():

    def __init__(self, interval, email, timeout=99999, threshold=Threshold(2,2)):
        self._interval = interval
        self._email = email
        self._timeout = timeout
        self._threshold = threshold
        self.tcpHealthChecker = None
        self.httpHealthChecker = None
        self.running = False

        self.initialize()
    
    @property
    def interval(self):
        return self._interval
    
    @property
    def email(self):
        return self._email
    
    @property
    def timeout(self):
        return self._timeout
    
    @property
    def threshold(self):
        return self._threshold
    
    @interval.setter
    def interval(self, interval):
        self.tcpHealthChecker.interval = interval
        self.httpHealthChecker.interval = interval
        self._interval = interval
    
    @email.setter
    def email(self, email):
        self.tcpHealthChecker.email = email
        self.httpHealthChecker.email = email
        self._email = email
    
    @timeout.setter
    def timeout(self, timeout):
        self.tcpHealthChecker.host.timeout = timeout
        self.httpHealthChecker.host.timeout = timeout
        self._timeout = timeout
    
    @threshold.setter
    def threshold(self, threshold):
        self.tcpHealthChecker.threshold = threshold
        self.httpHealthChecker.threshold = threshold
        self._threshold = threshold


    def initialize(self):
        http = HttpHost("https://tonto-http.cloudwalk.io",443, timeout=self.timeout)
        tcp = TcpHost("tonto-tcp.cloudwalk.io",3000, timeout=self.timeout)

        self.tcpHealthChecker = HealthChecker(tcp, self.threshold, self.interval, self.email)
        self.httpHealthChecker = HealthChecker(http, self.threshold, self.interval, self.email)
    
    def start(self):
        tcpHealthCheckerThread = threading.Thread(target=self.tcpHealthChecker.checkHealth, args=())
        httpHealthCheckerThread = threading.Thread(target=self.httpHealthChecker.checkHealth, args=())

        tcpHealthCheckerThread.start()
        httpHealthCheckerThread.start()

        self.running = True
    
    def stop(self):
        self.tcpHealthChecker.running = False
        self.httpHealthChecker.running = False

        self.running = False
