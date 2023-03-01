import os
import socket
import sys
import base64
import hmac
import secrets
import datetime
import time


PERSONAL_ID = '2493BB'
PERSONAL_SECRET = '49d2c0c4073ebd30d6392353340f2fc9'

def config_checker():
    if len(sys.argv) == 1:
        #print("no conf supplied")
        os._exit(1)
    try:
        file = open(sys.argv[1], "r")
    except:
        print(">>>ERROR when open file")
        os._exit(2)
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "spy_path":
            file.close()
            return 
    os._exit(2)
    
    
def client_getter():
    if len(sys.argv) == 1:
        print(">>>file doesn't exist")
        os._exit(1)
    try:
        file = open(sys.argv[1], "r")
    except:
        print(">>>ERROR when open file")
        os._exit(2)
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "client_port":
            PORT = line.split('\n')[0].split('=')[1]
            file.close()
            return PORT
    os._exit(2)
    

def server_getter():
    if len(sys.argv) == 1:
        print(">>>file doesn't exist")
        os._exit(1)
    try:
        file = open(sys.argv[1], "r")
    except:
        print(">>>ERROR when open file")
        os._exit(2)
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "server_port":
            PORT = line.split('\n')[0].split('=')[1]
            file.close()
            return PORT
    os._exit(2)


def inbox_getter():
    if len(sys.argv) == 1:
        print(">>>file doesn't exist")
        os._exit(1)
    try:
        file = open(sys.argv[1], "r")
    except:
        print(">>>ERROR when open file")
        os._exit(2)
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "spy_path":
            inbox_path = line.split('\n')[0].split('=')[1]
            file.close()
            return inbox_path
    os._exit(2)
    
    
def send_to_server(message, client_conn):
    message = message.strip("\n") + "\r\n"
    client_conn.sendall(message.encode())    
    
    
def send_to_client(message, server_conn):
    message = message.strip("\n") + "\r\n"
    server_conn.sendall(message.encode())

    
def setup_client_connection():
    SMTP_SERVER = ("127.0.0.1", int(server_getter()))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.connect(SMTP_SERVER)
    except:
        print("AC: Cannot establish connection", flush=True)
        os._exit(3)
    return sock


def data_receiver(data, mail_content):
    if data.strip() != ".":
        mail_content.append(data.strip("\r\n"))
        return
    mail_content.append(".")
    

def file_writer(sender, recipient, mail_content, inbox):
    months = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr':4,
         'may':5,
         'jun':6,
         'jul':7,
         'aug':8,
         'sep':9,
         'oct':10,
         'nov':11,
         'dec':12
        }
    inbox_path = inbox
    file_name = "unknown.txt"
    for line in mail_content:
        if line.split()[0] == "Date:":
            date = line.split()[1:]
            
            month = months[date[2].strip()[:3].lower()]
            
            date_time = datetime.datetime(int(date[3]), month, int(date[1]), int(date[4].split(":")[0]), int(date[4].split(":")[1]), int(date[4].split(":")[2]))
            
            time_stamp = time.mktime(date_time.timetuple())
            
            file_name = str(time_stamp).replace(".0", ".txt")
    file_name = inbox_path + '/' + file_name    
    with open(file_name, "w") as f:
        if sender:
            f.write("From: " + sender.split()[1].split(":")[1] + "\n")
        else:
            f.write("From:\n")
            
        if recipient:
            f.write("To: " + recipient.split()[1].split(":")[1] + "\n")
        else:
            f.write("To:\n")
            
        date = "Date:"
        for item in mail_content:
            if item.split()[0] == "Date:":
                date = item 
                mail_content.remove(item)
                            
        subject = "Subject:"    
        for item in mail_content:
            if item.split()[0] == "Subject:":
                subject = item       
                mail_content.remove(item) 
        
        f.write(date + "\n")
        f.write(subject + "\n")
        mail_content.remove("DATA")
        mail_content.remove(".")
        mail_content.remove("QUIT")
        for line in mail_content[:len(mail_content)]:
            f.write(line + "\n")
        #f.write(mail_content[len(mail_content)-1].strip("\n"))


def communicator():
    sock_as_client = setup_client_connection()
    mail_content = []
    inbox = inbox_getter()
    # sock_as_server = setup_server_connection()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", int(client_getter())))
        s.listen()
        conn, addr = s.accept()
        recording = False
        write_data = False
        quit = False
        with conn:
            while True:
                data = sock_as_client.recv(1024).decode()
                # print(">>>data = " + data)
                
                if not data:
                    print("AS: Connection lost" + data, flush=True, end='')
                    os._exit(3)
                else:
                    if "AUTH" in data:
                        first_message = "250 127.0.0.1"
                        first_message = first_message.strip("\n")
                        print("S: " + first_message + "\r\n", flush=True, end='')
                        second_message = "250 AUTH CRAM-MD5"
                        print("S: " + second_message + "\r\n", flush=True, end='')
                        print("AC: " + first_message + "\r\n", flush=True, end='')
                        print("AC: " + second_message + "\r\n", flush=True, end='')
                    else:
                        if not quit:
                            print("S: " + data, flush=True, end='')
                            print("AC: " + data, flush=True, end='')
                    # print(">>>before sending data")
                    conn.sendall(data.encode()) 
                    if quit:
                        print("S: " + "221 Service closing transmission channel\r\n", flush=True, end='')
                        print("AC: " + "221 Service closing transmission channel\r\n", flush=True, end='')
                        os._exit(3) 
                    # print(">>>welcome back")
                    data_from_client = conn.recv(1024).decode()
                    # print(">>>" + data_from_client)
                    if "MAIL FROM" in data_from_client: #for record sender/recipient
                        recording = True
                    if "DATA"  ==  data_from_client.strip():
                        write_data = True    
                    if not data_from_client:
                        print("AC: Connection lost" + data, flush=True, end='')
                        os._exit(3)   
                    else:
                        print("C: " + data_from_client, flush=True, end='')
                        print("AS: " + data_from_client, flush=True, end='')
                        send_to_server(data_from_client, sock_as_client)
                        if recording:
                            if "MAIL FROM" in data_from_client:
                                sender = data_from_client
                            if "RCPT TO" in data_from_client:
                                recipient = data_from_client
                            if write_data:    
                                data_receiver(data_from_client, mail_content)
                                # print(">>>Current mail_content = " + str(mail_content))
                        if "QUIT" in data_from_client:
                            if mail_content:
                                file_writer(sender, recipient, mail_content, inbox)       
                                quit = True

def main():
    config_checker()
    communicator()



if __name__ == '__main__':
    main()
