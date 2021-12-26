import socket
import pickle


class Network_API():
    def __init__(self):
        self.server = socket.gethostbyname(socket.gethostname())
        self.port = 5050
        self.addr = (self.server, self.port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(2048).decode()
        except:
            print("There is an error in the API connection")
            pass

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print("There is an error in sending or receiving data")
            print("[ERROR]: ", e)

    def send_request(self, request):
        """ Send a request to the server in form of a string """
        try:
            self.client.send(str.encode(request))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            #print("There is an error in sending the request")
            #print("[ERROR]: ", e)
            pass
