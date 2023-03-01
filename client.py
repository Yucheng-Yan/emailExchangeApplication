import os
import socket
import sys
from datetime import datetime

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
        if line.split('\n')[0].split('=')[0] == "send_path":
            file.close()
            return
    os._exit(2)
    
    
def port_getter():
    file = open(sys.argv[1], "r")
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "server_port":
            PORT = line.split('\n')[0].split('=')[1]
            file.close()
            return PORT

        
def check_status_code(data, expected_code):
    got_code = data.split()[0]
    if int(got_code) != int(expected_code):
        return False
    return True


def send_path_getter():
    file = open(sys.argv[1], "r")
    lines = file.readlines()
    for line in lines:
        if line.split('\n')[0].split('=')[0] == "send_path":
            send_path = line.split('\n')[0].split('=')[1]
            file.close()
            return send_path


def files_parser(path):
    ls = []
    list_dir = os.listdir(path)
    list_dir = [f.lower() for f in list_dir]
    for file in list_dir:
        ls.append(path + "/" + file)
    return sorted(ls)    


def recipient_ls(to_line):
    ls = []
    to_line = to_line.split(",")
    first_recipient = to_line[0].split(": ")[1]
    ls.append(first_recipient)
    i = 1
    while(i < len(to_line)):
        ls.append(to_line[i].strip())
        i += 1
    return ls


def recipient_sender(recipient_ls, sock):
    if recipient_ls:
        line_to_send = "RCPT TO:" + recipient_ls[0].strip() + "\r\n"
        sock.send(line_to_send.encode())
        print("C: " + line_to_send, flush=True, end='')
        recipient_ls.remove(recipient_ls[0])
        return recipient_ls 
    line_to_send = "DATA\r\n"
    sock.send(line_to_send.encode())
    print("C: " + line_to_send, flush=True, end='')
    


def sender(from_line, sock):
    #print(">>>from line" + from_line)#
    sender = from_line.split(": ")[1]
    line_to_send = "MAIL FROM:" + sender.strip() + "\r\n"
    sock.send(line_to_send.encode())
    print("C: " + line_to_send, flush=True, end='')
    return sender

    
def lines_breaker(lines_from_file, index, sock):
    line_to_send = lines_from_file[index].strip()
    if line_to_send.split()[0] == "To:" and len(recipient_ls(line_to_send)) > 1:
        line_to_send = "RCPT TO:" + recipient_ls(line_to_send)[index-1] + "\r\n"
        sock.send(line_to_send.encode())
    elif line_to_send.split()[0] == "Date:":
        line_to_send = "DATA" + "\r\n"
        sock.send(line_to_send.encode())
    print("C: " + line_to_send, flush=True, end='')
            
    
def setup_client_connection():
    SMTP_SERVER = ("127.0.0.1", int(port_getter()))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.connect(SMTP_SERVER)
    except:
        print("C: Cannot establish connection", flush=True)
        os._exit(3)
    return sock


def ehlo(sock):
    result = "EHLO 127.0.0.1\r\n"
    print("C: " + result, flush=True, end='')
    sock.send(result.encode())


def content_sender(content_line, sock):
    #print(">>>content_line = " + content_line)
    result = content_line.strip("\n") + "\r\n"
    print("C: " + result, flush=True, end='')
    sock.send(result.encode())
    

def dot_sender(sock):
    result = ".\r\n"
    print("C: " + result, flush=True, end='')
    sock.send(result.encode())
    

def quit_sender(sock):
    result = "QUIT\r\n"
    print("C: " + result, flush=True, end='')
    sock.send(result.encode())


def lines_from_file_updater(files_ls, i):
    with open(files_ls[i], 'r') as f: 
        lines_from_file = f.readlines()
    return lines_from_file
    
    
def ls_updator(lines_from_file): #return the recipients list of new email
    return recipient_ls(lines_from_file[1])
    

def file_checker(file):
    try:
        file = open(file, 'r')
    except:
        return False
    content = file.readlines()
    if(content[0].split()[0] == "From:"
       and content[1].split()[0] == "To:"
       and content[2].split()[0] == "Date:"
       and content[3].split()[0] == "Subject:"):
        return True
    return False

def communicator():
    file_is_valid = False
    i = 0
    
    while True:
        while not file_is_valid:
            files_ls = files_parser(send_path_getter())
            file_is_valid = file_checker(files_ls[i])
            if file_is_valid:
                with open(files_ls[i], 'r') as f: 
                    lines_from_file = f.readlines()
                ls = recipient_ls(lines_from_file[1]) #list of recipients
                quit = False 
                sock_is_open = True 
                sock = setup_client_connection()
            else:
                print("C: " + files_ls[i].replace("./", "/home/") + ": Bad formation\r\n", flush = True, end='')
                if ((i+1) < len(files_ls)):
                    i += 1
                    continue
                else:
                    os._exit(0)
        
        if sock_is_open:
            data = sock.recv(1024).decode()
        else:
            try:
                sock = setup_client_connection()
            except:
                print("C: Cannot establish connection", flush=True)
                os._exit(3)
            data = sock.recv(1024).decode()
            sock_is_open = True
        
        if not data:
            break
        else:
            print("S: " + data, flush=True, end='')

        if check_status_code(data, 220):
            ehlo(sock)
        elif check_status_code(data, 250) and quit:
            quit_sender(sock)        
        elif check_status_code(data, 250):
            if len(data.split()) == 2 or len(data.split("\r\n")) == 3: 
                #250 127.0.0.1
                sender(lines_from_file[0], sock)
                #lines_from_file.remove(lines_from_file[0])
            elif data.split()[1] == "Requested":
                #250 Requested mail action okay completed
                ls = recipient_sender(ls, sock) #update ls without first element
                continue
            lines_from_file.remove(lines_from_file[0])
        elif check_status_code(data, 354):
            if not lines_from_file:
                dot_sender(sock)
                quit = True
                continue
            elif lines_from_file[0].split()[0].strip() == "To:":
                lines_from_file.remove(lines_from_file[0])
            content_sender(lines_from_file[0], sock)
            lines_from_file.remove(lines_from_file[0])
        elif check_status_code(data, 221) and len(files_ls) > 1:
            i += 1
            if i < len(files_ls):
                lines_from_file = lines_from_file_updater(files_ls, i)
                ls = recipient_ls(lines_from_file[1])
            else:
                os._exit(0)
            quit = False    
            sock.close()
            sock_is_open = False     
        else:
            
            return
                                

def main():
    config_checker()
    communicator()
    


if __name__ == '__main__':
    main()
    
    