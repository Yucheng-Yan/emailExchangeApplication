import os
import socket
import sys
import base64
import hmac
import secrets
import datetime
import time
import signal


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
        if line.split('\n')[0].split('=')[0] == "inbox_path":
            file.close()
            return
    os._exit(2)
    
def port_getter():
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
        if line.split('\n')[0].split('=')[0] == "inbox_path":
            inbox_path = line.split('\n')[0].split('=')[1]
            file.close()
            return inbox_path
    os._exit(2)
    
    
def send_print(message, conn):
    message = message.strip("\n") + "\r\n"
    print("S: " + message, flush=True, end="")
    conn.sendall(message.encode())


def error_501(conn):
    send_print("501 Syntax error in parameters or arguments", conn)


def error_503(conn):
    send_print("503 Bad sequence of commands", conn)
        
        
def check_status_code(data, expected_code):
    data = data.strip()
    got_code = data.split()[0][0:4]
    if got_code != expected_code:
        return False
    return True


def ehlo(data, conn, status):
    if(len(data.split()) == 2 and 
       len(data.split(" ")[1].split(".")) == 4):
        first_message = "250 127.0.0.1"
        first_message = first_message.strip("\n")
        print("S: " + first_message + "\r\n", flush=True, end='')
        second_message = "250 AUTH CRAM-MD5"
        print("S: " + second_message + "\r\n", flush=True, end='')
        message = first_message + "\r\n" + second_message + "\r\n"
        conn.sendall(message.encode())
        status = "s3"
        return status
    else:
        error_501(conn)
        status = "s1"
        return status
    

def auth(conn):
    challenge = secrets.token_hex(16).encode() #b'abfd32f6-a674-4589-b368-a1206d8be1f0'
    challenge = base64.b64encode(challenge)
    result = "334 ".encode() + challenge + "\r\n".encode()
    print("S: 334 " + challenge.decode() + "\r\n", flush = True, end='')
    conn.sendall(result)
    return ["s5", challenge]


def auth_checker(data, conn, challenge):    
    data = data.strip("\r\n")
    data = base64.b64decode(data)
    challenge_decoded = base64.b64decode(challenge)
    h = hmac.new(PERSONAL_SECRET.encode(), challenge_decoded, "md5")
    h = h.hexdigest()
    answer = PERSONAL_ID + ' ' + h
    answer = base64.b64encode(answer.encode())
    answer = base64.b64decode(answer)
    # print(">>>data = " + data.decode())
    # print(">>>answer = " + answer.decode())
    if data == answer:
        send_print("235 Authentication successful", conn)
        return "s3"
    else:
        send_print("535 Authentication credentials invalid", conn)
        return "s3"


def mail(data, conn, status):
    if " " in data:
        if(len(data.split()) == 2):
            if(len(data.split()[1].split(":")) == 2):
                sender = data.split()[1].split(":")[1]
                if("<" in sender
                and ">" in sender
                and "@" in sender
                and "." in sender
                and "@-" not in sender
                and "!" not in sender
                and sender[1].isalpha()
                and "-." not in sender
                and ".-" not in sender):
                    return_values = ["s8", data.strip("\r\n")]
                    return return_values
    error_501(conn)
    return [status, '']
    

def rset(data, conn, status):
    if(data == "RSET\r\n"):
        send_print("250 Requested mail action okay completed", conn)
        return "s3"
    else:
        error_501(conn)
        return status
    

def rcpt(data, conn, status):
    if " " in data:
        if(len(data.split()) == 2):
            if(len(data.split()[1].split(":")) == 2):
                recipient = data.split()[1].split(":")[1]
                if("<" in recipient
                and ">" in recipient
                and "@" in recipient
                and "." in recipient
                and "-" not in recipient
                and "!" not in recipient):
                    send_print("250 Requested mail action okay completed", conn)
                    return_values = ["s11", data.strip("\r\n")]
                    return return_values
                    
    error_501(conn)
    return [status, '']


def data_receiver(data, conn, status, mail_content):
    if data.strip() != ".":
        send_print("354 Start mail input end <CRLF>.<CRLF>", conn)
        mail_content.append(data.strip("\r\n"))
        return ["s13", mail_content]
    send_print("250 Requested mail action okay completed", conn)
    mail_content.append(".")
    return ["s3", mail_content]


def file_writer(sender, recipient, mail_content):
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
    inbox_path = inbox_getter()
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
            
        if mail_content[0].split()[0] == "Date:":
            date = mail_content[0]
        else:
            date = "Date:\n"
            
        if mail_content[1].split()[0] == "Subject:":
            subject = mail_content[1] #[:len(mail_content[1])-1]
        else:
            subject = "Subject:\n"
        
        f.write(date + "\n")
        f.write(subject + "\n")
        
        for line in mail_content[2:len(mail_content)-2]:
            f.write(line + "\n")
        #f.write(mail_content[len(mail_content)-2])


def noop(data, conn):
    # print("data = " + data)
    # print(len(data.strip()))
    if(data == "NOOP\r\n"):
        send_print("250 Requested mail action okay completed", conn)
    else:
        error_501(conn)
    

def signal_handler(sig, frame):
    print("S: SIGINT received, closing\r\n", flush=True, end='')
    message = "421 Service not available, closing transmission channel" + "\r\n"
    os._exit(0)

        
def quit(data, conn):
    if data == "QUIT\r\n":
        send_print("221 Service closing transmission channel", conn)
        return True
    else:
        error_501(conn)
        return False
        
    
def communicator():
    HOST = "127.0.0.1"  
    status = "s0"
    sender = 0
    recipient = 0
    mail_content = []
    data = ""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, int(port_getter())))
        s.listen()
        conn, addr = s.accept()
        with conn:
            conn.sendall("220 Service ready\r\n".encode())
            print("S: 220 Service ready\r\n", flush=True, end='')
            status = "s1"
            while True:
                try:
                    data = conn.recv(1024).decode()
                except:
                    print("S: Connection lost\r\n", flush=True, end='')
                    break

                if not data:
                    print("S: Connection lost\r\n", flush=True, end='')
                    break
                else:
                    print("C: " + data, flush=True, end='')
                
                #Commands that can be called anytime
                if data.strip() == "SIGINT":
                    signal_handler()

                    
                elif check_status_code(data, "QUIT"):
                    if status == "s3" and mail_content:
                        try:
                            file_writer(sender, recipient, mail_content)
                            mail_content = []
                        except:
                            pass
                    if(quit(data, conn)):
                        break
                    
                elif(check_status_code(data, "RSET")
                    and status != "s12"
                    and status != "s13"):
                    status = rset(data, conn, status)
                    
                elif(check_status_code(data, "NOOP")
                    and status != "s12"
                    and status != "s13"):
                    noop(data, conn)
                

                    
                    
                #status 1   
                elif status == "s1":
                    # print(">>>status = " + status)#
                    if check_status_code(data, "EHLO"):
                        status = ehlo(data, conn, status)
                    elif check_status_code(data, "RCPT"):
                        error_503(conn)
                    elif check_status_code(data, "MAIL"):
                        error_503(conn)
                    else:
                        error_501(conn)
                        
                #status 3  
                elif status == "s3":
                    # print(">>>status = " + status)#
                    if check_status_code(data, "EHLO"):
                        status = ehlo(data, conn, status)
                    elif check_status_code(data, "MAIL"):
                        return_values = mail(data, conn, status)
                        status = return_values[0]
                        sender = return_values[1] # in the form of FROM: <>
                        if status == "s8":
                            send_print("250 Requested mail action okay completed", conn)
                            status = "s9"
                    elif check_status_code(data, "AUTH"):
                        return_values = auth(conn)
                        status = return_values[0]
                        challenge = return_values[1]
                    elif check_status_code(data, "RCPT"):
                        error_503(conn)
                    elif check_status_code(data, "DATA"):
                        error_503(conn)
                    else:
                        error_501(conn)
                
                #status 5
                elif status == "s5":
                    status = auth_checker(data, conn, challenge)
                        
                #status 9 & 11
                elif status == "s9" or status == "s11":
                    if check_status_code(data, "MAIL"):
                        error_503(conn)
                    elif check_status_code(data, "RCPT"):
                        return_values = rcpt(data, conn, status)
                        status = return_values[0]
                        recipient = return_values[1]
                        # print(">>>status = " + status)
                    elif check_status_code(data, "DATA"):
                        # print(">>>ENTER DATA")
                        send_print("354 Start mail input end <CRLF>.<CRLF>", conn)
                        status = "s12"
                        
                #status 12 & 13
                elif status == "s12" or status == "s13":
                    return_values = data_receiver(data, conn, status, mail_content)
                    status = return_values[0]
                    mail_content = return_values[1]
                

def main():
    signal.signal(signal.SIGINT, signal_handler)
    config_checker()
    communicator()


if __name__ == '__main__':
    main()