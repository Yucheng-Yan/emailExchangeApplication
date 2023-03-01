# Email Exchange Application

Implement in Python some email exchange applications that supports the `SMTP-CRAM` protocol. This includes a client, a server and an eavesdropper (middle-man attacker), which can apply MitM attack to the authentication mechanism. 

Assume all programs are supposed to be run and tested locally and they are not required to be extensible to support TCP connection via the Internet or to be used in real world. No actual data should be sent and received from the Internet, and everything should be contained in the local loopback. We also assume any syntactically valid message under the protocol can be accepted. E.g., No actual check is needed on any email or IP address, we accept any syntactically valid messages including addresses.

The communication between the email exchange applications has to follow a popular protocol for email exchanging, the Simple Mail Transfer Protocol (`SMTP`) protocol with one authentication extension (`CRAM-MD5`), the SMTP Service Extension for Authentication by Challenge-Response Authentication Mechanism. The authentication type associated is called `CRAM-MD5` and the full protocol is named `SMTP-CRAM`.

However, `CRAM-MD5` only allows the server to verify the client and doesn’t provide any server authentication, therefore its usage is limited and less preferable than other stronger mechanisms. To demonstrate `CRAM-MD5` indeed has its weakness, the eavesdropper should be implemented and a MitM attack can be performed.

On the high level, the following needs to be implemented:

- All programs are capable of:
    - Log all `socket` transactions in a specific format and output to `stdout`.
- The `SMTP-CRAM` server is capable of:
    1. Prepare for any incoming client connection.
    2. Receive emails from a client and save to disk.
    3. Additionally, allow client authentication.
    4. Allow multiple clients to connect simultaneously.
    5. Termination upon receiving a `SIGINT` signal.
- The `SMTP-CRAM` client is capable of:
    1. Read mail messages on disk.
    2. Send emails to the server.
    3. Additionally, allow client authentication.
    4. Termination after finishing sending all emails.
- The `SMTP-CRAM` eavesdropper (middle-man attacker) can do active eavesdropping between a pair of given server (E.g.,the real server) and client (E.g.,the real client). It can intercept all `socket` messages passing between the real server and the real client without being discovered. This means it is capable of:
    1. Prepare for being connected to by the real client and connecting to the real server.
    2. Capture the email sent by the real client and save to disk, without altering the content.
    3. Additionally, comprise any client authentication.
    4. Termination.

The project has four tasks, the three tasks are:

1. Implement a client that supports the `SMTP-CRAM` protocol.
2. Implement a server that supports the `SMTP-CRAM` protocol.
3. Implement an eavesdropper (middle-man attacker) that secretly relays the communications between the client and the server that supports the `SMTP-CRAM` protocol.

## File formations

### Configuration files

As with most web servers, the configuration files need to have porting information. Specifically:

- The server configuration should have a `server_port`, and it awaits incoming TCP registration connections at the `localhost` on the `server_port`. It also has a `inbox_path`, a directory path to save any emails received.
- The client configuration should have a `server_port`. It sends outgoing TCP registration connections to the `localhost` at the `server_port`. It also has a `send_path`, a directory path to read any emails to be sent.
- The eavesdropper configuration should have a `server_port` and a (different) `client_port`. It relays information between the server and the client. Note, the client will be launched by having its `server_port` being the `client_port` of the eavesdropper. It also has a `spy_path`, a directory path to save any emails captured.

The configuration file is a simple text file where each property is assigned to a value. When reading the configuration file, the program needs to retrieve each of needed properties and their value from the file.

- `server_port` - integer, the port the server listens on. Greater than 1024.
- `client_port` - integer, the port the server listens on. Greater than 1024. If present, should be different from `server_port`.
- `_path` - string, a valid and writable path on disk. If multiple paths present, should be different from each other.

### Configuration file example

```
server_port=1025client_port=1026inbox_path=~/inboxsend_path=~/sendspy_path=~/spy
```

### Email transaction text file

It is encoded by ASCII in a human-readable manner, it has to have the following fields and in the exact order shown:

- Sender information.
    - One line and non-empty.
    - Email address in `<>` bracket.
    - `From: <someone@domain.com>`
- Recipent(s) information.
    - One line and non-empty.
    - Email address in `<>` bracket.
    - Separated by `,` if there are multiple address supplied.
    - `To: <other@domain.com>`
    - `To: <other@domain.com>,<other.other@domain.com>`
- Sending time.
    - One line and non-empty.
    - Date and time in RFC 5322 format.
    - `Mon, 14 Aug 2006 02:34:56 -0600`
- Subject.
    - One line and non-empty.
- Body.
    - Multiple lines in ASCII.

Note that to to ensure text files are encoded in ASCII, one could use a primitive text editor with input methods disabled. E.g., CJK language characters are not ASCII.

### Email transaction text file example

```
From: <bob@bob.org>To: <alice@example.com>,<me@carol.me>Date: Mon, 14 Sep 1987 23:07:00 +1000Subject: Frist Electronic Mail from Bob to Alice and CarolAcross the Exosphere we can reach every corner on the Moon.P.S. THIS IS NOT A SPAM
```

## Program behaviours

### All programs

### Logging

Log all `socket` transactions in a specific format and output to `stdout`. Each program will log the `socket` data **chronologically**, and the identity of the apparent sender. For multiline messages, every `CRLF` implies a line break in the log. Note, the eavesdropper always knows who the client and server are, however both the client and server are unaware if they are connected to an eavesdropper or not.

### Logging example

Suppose the client connects to the server, then first sends `abc` to the server and the server replies `cba` after receiving `abc`. Both the client and the server should output the following in `stdout`.

```
C: abcS: cba
```

Suppose the client connects to the eavesdropper (attacker), which it regards as the server, then first sends `abc` to the eavesdropper. The eavesdropper connects to the server and relays (sends) `abc` to the server. After receiving `abc`, the server replies `cba` to the eavesdropper, which it regards as the client. After receiving `abc`, the eavesdropper replies `cba` to the client.

Because the eavesdropper does not change the message, both the client and server write the same output to `stdout`, identical to the above example. However, the eavesdropper knows more:

```
C: abcAS: abcS: cbaAC: cba
```

### Server

A server should:

1. Read the command line arguments. The configuration file path should be supplied. If not, terminate the program with exit code `1`. Parse the configuration file. If any needed property is missing or its value is invalid, terminate the program with exit code `2`. To be specific, if the program cannot write files to the `inbox_path` path, terminate the program with exit code `2`; if the program failed to bind to the given port, terminate the program with exit code `2`.
2. Prepare for any incoming client connection. Accept and establish a TCP connection from a client. Whenever the client disconnects unexpectedly, log `S: Connection lost` to `stdout` but do not terminate the program.
3. Receive an email from a client. Receive request data from and send response data to a client over TCP. When an email transaction is finished, parse and save the email transaction to a text file in the email transaction text format. The file should be named after the Unix timestamp of the sending time. If any field (e.g., subject, date) is missing or invalid, do not raise an error and keep the field empty. If the sending time is missing or invalid, the file should be named `unknown.txt`. If an email to be saved should share the same file name with another existing file on disk, overwrite the existing file.
4. Additionally, allow client authentication. When `SMTP-CRAM` is implemented (e.g., `CRAM-MD5` is included in the server response of `EHLO`), send the challenge data to the client and authenticate the client before accepting the email. If the client has been verified for authentication in this session, prefix the file name of the email, which is received after the authentication, with `auth.`.
5. End a client session when the client sends a `QUIT` request.
6. (Optionally) Allow multiple clients to connect simultaneously by multi-processing technique (explicitly by `fork`ing, not multi-threading).
7. Termination. Upon receiving a `SIGINT` signal, print `S: SIGINT received, closing` to `stdout`, and properly terminates ongoing client sessions and itself with with exit code `0`.

Note, the server needs to be robust, meaning not only it can handle requests from the designed client, but also it can handle requests with all possible errors in the expected way without crashing.

### Multi-process server

- This section is related to the bonus task.

If the server can handle multiple connections from clients simultaneously, it needs to spawn multiple child processes to handle each client connection.

In this assignment specifically, there are a few additional requirements on implementation are needed:

1. `fork` implementation. Multi-threading implementation is not allowed. Only multi-processing implementation by `os.fork()` is allowed. Wrong implementation will result in manual deduction.
2. Instant `fork` after connection establishment. It is required that once the server `main` process (the process that is launched manually by the user) accepts a client connection, it should `fork` immediately to a server `child` process. In other words, the main process should only wait for new client connections and accept them. It will let its children handle the real communication in each server-client session.
3. Prefix with `[PID][ORDER]`. The bahaviour of logging and saving need a minor change. This helps the user to differentiate between the server `child` processes. Instead of using the simple convention `C:` and `S:`, the `child` processes should add a prefix `[PID][ORDER]`. When saving an email transaction file, also add a prefix `[PID][ORDER]` to the file name.
4. Server `child` process quits when client `QUIT`s. Unlike single process server, a server `child` terminates when the client `QUIT` and it sends a `221` reply.
5. Termination. When `main` receives a `SIGINT`, it should immediately stop accepting new clients and signal all alive `child` processes by `SIGINT` to force them to terminate. After ensuring all `child`s’ terminations, `main` terminates itself. Assume that no `child` process should be signaled by `SIGINT` externally, but it is nice to make the `main` server tolerant unexceptedly terminated `child`.

For example, if the server has received two connections from two clients, it may log something like this:

```
[110][01]S: 220 Service ready[115][02]S: 220 Service ready[110][01]C: EHLO 127.0.0.1[110][01]S: 250 127.0.0.1[115][02]C: EHLO 127.0.0.1[110][01]S: 250 AUTH CRAM-MD5[115][02]S: 250 127.0.0.1[115][02]S: 250 AUTH CRAM-MD5
```

Where `[110][01]` means the server `main` process spawned the first (`[01]`) `child` process to handle a client, and the `[01]` `child` has process ID `110`. Similarily, we know `main` forked to `[02]` `child` with PID `115`. The `order` should never decrement and increment by 1 when a new connection is established. It won’t decrement when a server `child` process terminates.

Recall the `fork` and `exec` practices in Week 3 lab, the order of the logs among `child` processes might not be completely determinastic, but the order has to deterministic for a specific `child` process.

### Client

A client should:

1. Read the command line arguments. The configuration file path should be supplied. If not, terminate the program with exit code `1`. Parse the configuration file. If any needed property is missing or its value is invalid, terminate the program with exit code `2`. To be specific, if the program cannot read files in the `send_path` path, terminate the program with exit code `2`.
2. Prepare one mail message to be sent. Read and parse an email transaction text files in `send_path`. Only attempt to read regular files in the `send_path`. If there are more than one files, queue them in the dictionary order of the file names. Check and send only one at a time. Whenever an email transaction text cannot be parsed due to bad formation, log `C: <filepath>: Bad formation` to `stdout` and continue to the next file without retry.
3. Attempt a TCP connection to a server. If failed, log `C: Cannot establish connection` to `stdout` and terminate the client with exit code `3`. Whenever the server disconnects unexpectedly, log `C: Connection lost` to `stdout` and terminate the client with exit code `3`.
4. Send an email to the server. Send request data to and receive response data from and a server over TCP. The request data needs to be determined (compiled) by the client itself. That is, based on a valid email transaction text, the client needs to decide automatically what commands to send with what additional parameters. No manual input can be accepted by the client when it starts executing. Please see the examples at the end of this section. Alternatively, take Week 10 Lab Task 5 an example.
5. Additionally, allow client authentication. When `SMTP-CRAM` is implemented (e.g., `CRAM-MD5` is included in the server response of `EHLO`) and the email transaction text file absolute path has `AUTH` (case-insensitive) in its absolute path file, send `AUTH` to the server immediately after `EHLO`. Send the answer (to the challenge) data to the server and prove its authentication to the server before sending the email.
6. Termination. Send a `QUIT` request after finishing sending one email, and disconnect after receiving a `221` reply. Reconnect to continue if there exists more to send in the queue, e.g., go to step 2. When finishing sending all emails, terminate with exit code `0`.

### Eavesdropper

An eavesdropper should:

1. Read the command line arguments. The configuration file path should be supplied. If not, terminate the program with exit code `1`. Parse the configuration file. If any needed property is missing or its value is invalid, terminate the program with exit code `2`. To be specific, if the program cannot write files to the `spy_path` path, terminate the program with exit code `2`.
2. Prepare for being connected to by the real client and connecting to the real server. Accept and establish a TCP connection from the real client. Attempt a TCP connection to the real server. If failed to connect to the real server, log `AS: Cannot establish connection` to `stdout` and terminate the client with exit code `3`. Whenever the real server disconnects unexpectedly, log `AS: Connection lost` to `stdout` and terminate the client with exit code `3`. Whenever the client disconnects unexpectedly, log `AC: Connection lost` to `stdout` but do not terminate the program.
3. Capture the email sent by the real client, log the message and relay to the real server. Receive request data from and send response data to the real client and the real server over TCP. Output all `socket` transactions to `stdout`, write other internal information and error to `stdout`. When an email transaction is finished, parse and save the email transaction to a text file as if it is a server.
4. Additionally, comprise any client authentication. When `SMTP-CRAM` is implemented, relay the real server challenge to the real client, steal the valid answer to the real challenge, and relay the valid answer to the real server. In such a way it can pretend to be the real client as it steals the valid authenticated answer.
5. Termination. Send a `QUIT` request to the real server after receiving a `QUIT` from the real client, then terminate itself with exit code `0`.

### Non-AUTH example

Assume we have a configuration file `conf.txt` and only one email transaction text file `email.txt` in `~/send`. The two files inherit the exemplars in the “File formations” section.

First, to set up the server, we can run in Bash

```bash
python3 server.py conf.txt
```

Wait a few second, we then set up the client in Bash.

```bash
python3 client.py conf.txt
```

Then the client will look into `~/send`, read and parse the email, the log the following

```
S: 220 Service readyC: EHLO 127.0.0.1S: 250 127.0.0.1S: 250 AUTH CRAM-MD5C: MAIL FROM:<bob@bob.org>S: 250 Requested mail action okay completedC: RCPT TO:<alice@example.com>S: 250 Requested mail action okay completedC: RCPT TO:<me@carol.me>S: 250 Requested mail action okay completedC: DATAS: 354 Start mail input end <CRLF>.<CRLF>C: Date: Mon, 14 Sep 1987 23:07:00 +1000S: 354 Start mail input end <CRLF>.<CRLF>C: Subject: Frist Electronic Mail from Bob to Alice and CarolS: 354 Start mail input end <CRLF>.<CRLF>C: Across the Exosphere we can reach every corner on the Moon.S: 354 Start mail input end <CRLF>.<CRLF>C: P.S. THIS IS NOT A SPAMS: 354 Start mail input end <CRLF>.<CRLF>C: .S: 250 Requested mail action okay completedC: QUITS: 221 Service closing transmission channel
```

Note, the client CANNOT perform authentication if the `EHLO` reply does not contain `S: 250 AUTH CRAM-MD5`. However, such server can be considered an incomplete assignment server. For the assignment server, it should ALWAYS send `250 AUTH CRAM-MD5`. For the assignment client, it is up to the client to `AUTH` or not, depending on whether `auth` presents in the absoluate path of a sending file.

On the other hand, the server should log exact same thing. In addition, an email transaction text `~/inbox/558623220.txt` should be saved before the server processes `QUIT` sent by the client. The content of the `~/inbox/558623220.txt` should be exactly the same as `~/send/email.txt`.

After sending the first and the only email in `~/send`, the client indeed should `QUIT`.

The server, however, should run indefinitely until receiving a `SIGINT` signal. If there are multiple children spawned by the server, all children need to be terminated gracefully as well.

### AUTH example

With the same set up as the previous example, except the only email transaction text file is named `auth-email.txt`, the client will log the following

```
S: 220 Service readyC: EHLO 127.0.0.1S: 250 127.0.0.1S: 250 AUTH CRAM-MD5C: AUTH CRAM-MD5S: 334 YWJmZDMyZjYtYTY3NC00NTg5LWIzNjgtYTEyMDZkOGJlMWYwC: Ym9iIDQ3MTUwNGIxOTcwYzk0ZjJmYjQ4Y2E4ODkwY2Y1ZGRmS: 235 Authentication successfulC: MAIL FROM:<bob@bob.org>S: 250 Requested mail action okay completedC: RCPT TO:<alice@example.com>S: 250 Requested mail action okay completedC: RCPT TO:<me@carol.me>S: 250 Requested mail action okay completedC: DATAS: 354 Start mail input end <CRLF>.<CRLF>C: Date: Mon, 14 Sep 1987 23:07:00 +1000S: 354 Start mail input end <CRLF>.<CRLF>C: Subject: Frist Electronic Mail from Bob to Alice and CarolS: 354 Start mail input end <CRLF>.<CRLF>C: Across the Exosphere we can reach every corner on the Moon.S: 354 Start mail input end <CRLF>.<CRLF>C: P.S. THIS IS NOT A SPAMS: 354 Start mail input end <CRLF>.<CRLF>C: .S: 250 Requested mail action okay completedC: QUITS: 221 Service closing transmission channel
```

Note, the client performs authentication because the `EHLO` reply contains `S: 250 AUTH CRAM-MD5`.

On the other hand, the server should log the exact same thing. In addition, an email transaction text `~/inbox/auth.558623220.txt` should be saved before the server processes `QUIT` sent by the client. The content of the `~/inbox/auth.558623220.txt` should be exactly the same as `~/send/email.txt`.

After sending the first and the only email in `~/send`, the client indeed should `QUIT`. In the case there are more than one email text files, send them one at a time by dictionary order of the file names.

### Eavesdropper example

The saving email behaviour eavesdropper should be same as a server. The logging behaviour is different from a server however stated clear before in the “Logging example”. When testing the eavesdropper, make sure to launch the programs in the following order:

1. Real server
2. The eavesdropper
3. Real client

## `SMTP-CRAM` Order of Events

### Session Initiation

An SMTP session is initiated when a client opens a connection to a server and the server responds with an opening message. The server includes identification of the software and version information in the connection greeting reply after the `220` code. E.g.

```
S: 220 Service readyC: EHLO 127.0.0.1
```

### Client Initiation

Once the server has sent the welcoming message and the client has received it, the client normally sends the EHLO command to the server, indicating the client’s identity.

In the EHLO command the host sending the command identifies itself; the command may be interpreted as saying “Hello, I am ”.

### Mail Transactions

There are three steps to SMTP mail transactions. The transaction starts with a MAIL command which gives the sender identification. In general, the MAIL command can be sent only when no mail transaction is in progress, otherwise an error will occur. A series of one or more RCPT commands follows giving the email recipient information. Then a DATA command initiates transfer of the mail data and is terminated by the “end of mail” data indicator, which also confirms the transaction.

Mail transaction commands MUST be used in the order discussed above.

### Terminating Sessions and Connections

An SMTP connection is terminated when the client sends a QUIT command. The server responds with a positive reply code, after which it closes the connection.

An SMTP server MUST NOT intentionally close the connection except:

- After receiving a QUIT command and responding with a `221` reply.
- After detecting the need to shut down the SMTP service (E.g.,When the server receives a `SIGINT` signal) and returning a `421` response code. This response code can be issued after the server receives any command or, if necessary, asynchronously from command receipt (on the assumption that the client will receive it after the next command is issued).

In particular, a server that closes connections in response to commands that are not understood is in violation of this specification. Servers are expected to be tolerant of unknown commands, issuing a `500` reply and awaiting further instructions from the client.

An SMTP server which is forcibly shut down via external means SHOULD attempt to send a line containing a `421` response code to all connected SMTP clients before exiting. The SMTP client will normally read the `421` response code after sending its next command.

SMTP clients that experience a connection close, reset, or other communications failure due to circumstances not under their control (in violation of the intent of this specification but sometimes unavoidable) SHOULD, to maintain the robustness of the mail system, treat the mail transaction as if a `451` response had been received and act accordingly.

### Order restriction

There are restrictions on the order in which commands may be used.

A session that will contain mail transactions MUST first be initialized by the use of the `EHLO` command.

An `EHLO` command MAY be issued by a client later in the session. If it is issued after the session begins, the SMTP server MUST clear all buffers and reset the state exactly as if a `RSET` command had been issued. In other words, the sequence of `RSET` followed immediately by `EHLO` is redundant, but not harmful other than in the performance cost of executing unnecessary commands.

The `RSET` commands can be used at any time during a session, or without previously initializing a session. SMTP servers processes it normally (that is, not return a `503` code) even if no `EHLO` command has yet been received.

The `MAIL` command begins a mail transaction. Once started, a mail transaction consists of a transaction beginning command, one or more RCPT commands, and a `DATA` command, in that order. A mail transaction may be aborted by the `RSET` (or a new `EHLO`) command. There may be zero or more transactions in a session. `MAIL` command MUST NOT be sent if a mail transaction is already open, i.e., it should be sent only if no mail transaction had been started in the session, or it the previous one successfully concluded with a successful `DATA` command, or if the previous one was aborted with a `RSET`.

If the transaction beginning command argument is not acceptable, a `501` failure reply MUST be returned, and the SMTP server MUST stay in the same state. If the commands in a transaction are out of order to the degree that they cannot be processed by the server, a `503` failure reply MUST be returned, and the SMTP server MUST stay in the same state. E.g.:

- If a `RCPT` command appears without a previous MAIL command, the server MUST return a `503` “Bad sequence of commands” response.
- If there was no `MAIL`, or no `RCPT` command, or all such commands were rejected, the server returns a “command out of sequence” (`503`) reply in response to the `DATA` command.

The last command in a session MUST be the `QUIT` command. The `QUIT` command cannot be used at any other time in a session but be used by the client SMTP to request connection closure, even when no session opening command was sent and accepted.

## `SMTP-CRAM` Request and Response

Application data is exchanged following a sequence of request-response messages.

**Every client request must generate exactly one server response.** **Except the first client request, every client can only request again after receiving the server response regarding its previous request.**

### Request in general

A `SMTP-CRAM` request is consists of a command name and followed by parameters. The request command name is specified in the `<COMMAND>`. The parameters, if any, are separated by a single space after the command name. All fields are case-sensitive.

The maximum of a command line total length is 1024 bytes. This includes the command word, the parameter, and `<CRLF>`.

```
<COMMAND> [PARAMETER]...
```

In ABNF syntax:

```
REQUEST             =   COMMAND                        *[ SP PARAMETER ]                        CRLF
```

We add restrictions below:

```
COMMAND             =   "EHLO" /                        ;; HELLO                        "MAIL" /                        ;; MAIL                        "RCPT" /                        ;; RECIPIENT                        "RSET" /                        ;; RESET                        "NOOP" /                        ;; NOOP                        "QUIT" /                        ;; QUIT                        "AUTH" /                        ;; AUTHENTICATEPARAMETER           = *OCTET
```

### Response in general

A `SMTP-CRAM` response is consists of a three-digit number (transmitted as three numeric characters) followed by some text unless specified otherwise in this document. The number can be used to determine what state the client is at; the text is for the human user. Exceptions are as noted elsewhere in this document. In the general case, the text is context dependent, so there are varying texts for each reply code. The response code is specified in the `<CODE>`. The parameters, if any, are separated by a single space after the command name. All fields are case-sensitive.

```
<CODE> [PARAMETER]...
```

In ABNF syntax:

```
RESPONSE            =   CODE                        *[ SP PARAMETER *CRLF]                        CRLF
```

We add restrictions below:

```
CODE                =   "220" /                        ;; Service ready                        "221" /                        ;; Service closing transmission channel                        "235" /                        ;; Authentication succeeded                        "250" /                        ;; Requested mail action okay, completed                        "334" /                        ;; Server BASE64-encoded challenge                        "354" /                        ;; Start mail input; end with <CRLF>.<CRLF>                        "421" /                        ;; Service not available, closing transmission channel                        ;; (This may be a reply to any command if the service knows it must shut down)                        "500" /                        ;; Syntax error, command unrecognized                        "501" /                        ;; Syntax error in parameters or arguments                        "503" /                        ;; Bad sequence of commands                        "504" /                        ;; Command parameter not implemented                        "535" /                        ;; Authentication credentials invalidPARAMETER           = *OCTET
```

Each command is listed with its usual possible replies. The prefixes used before the possible replies are “IM” for intermediate, “SC” for success, and “ER” for error. Note that error `421` can be responded to any commands if the server knows it is going to be terminated before the clients disconnect, therefore `421` is omitted.

```
CONNECTION ESTABLISHMENT    SC: 220EHLO    SC: 250, 501MAIL    SC: 250    ER: 501, 503RCPT    SC: 250    ER: 501, 503DATA    IM: 354 -> data -> SC: 250    ER: 501, 503RSET    SC: 250    ER: 501NOOP    SC: 250    ER: 501AUTH    IM: 334 -> data -> SC: 235                       ER: 535    ER: 501, 504QUIT    SC: 221    ER: 501
```

### Error code explanation

`500`: For the command name that cannot be recognized or the “request is too long” case. Note, if request is too long, it very likely that the longer-than-1024-bytes part cannot be recognized as a valid command.

```
500-response            = "500" SP "Syntax error, command unrecognized" CRLF
```

`501`: Syntax error in command or arguments. Commands that are specified in this document as not accepting arguments (`DATA`, `RSET`, `QUIT`) return a `501` message when arguments are supplied.

```
501-response            = "501" SP "Syntax error in parameters or arguments" CRLF
```

`503`: For a “Bad sequence of commands”, previously discussed in “Order of commands” section.

```
503-response            = "503" SP "Bad sequence of commands" CRLF
```

`504`: This response to the `AUTH` command indicates that the authentication failed due to unrecognized authentication type.

```
504-response            = "504" SP "Unrecognized authentication type" CRLF
```

`535`: This response to the `AUTH` command indicates that the authentication failed due to invalid or insufficient authentication credentials.

```
535-response            = "535" SP "Authentication credentials invalid" CRLF
```

### `EHLO`

### `EHLO` example

```
S: 220 Service readyC: EHLO 127.0.0.1S: 250 127.0.0.1S: 250 AUTH CRAM-MD5
```

### `EHLO` request

The hello request.

After receiving `220` reply from the server, a client starts an SMTP session by issuing the `EHLO` command. The server will give either a successful response, a failure response, or an error response. In any event, a client MUST issue EHLO before starting a mail transaction. This command and a `250` reply to it, confirm that both the client and the server are in the initial state.

Log example:

```
C: EHLO 127.0.0.1
```

In ABNF syntax,

```
ehlo-request                = "EHLO" SP IPv4-address CRLF
```

### `EHLO` response

The hello response.

The server will give either a successful response, or an error response. If `IPv4-address` is invalid, the server reports a `501-response`.

The successful response to `EHLO` request is a multiline reply. Each line starts with a successful code (`250`) followed by a space and other parameters separated by a space.

Log example:

```
S: 250 127.0.0.1S: 250 AUTH CRAM-MD5
```

In ABNF syntax,

```
ehlo-ok-response            =   "250" SP IPv4-address                                CRLF                                "250" SP "AUTH" SP "CRAM-MD5"                                CRLF
```

Where `IPv4-address` is the IPv4 address the address of the client, should always be `127.0.0.1`.

Note, an `EHLO` command MAY be issued by a client later in the session. If it is issued after the session begins, the SMTP server MUST clear all buffers and reset the state exactly as if a `RSET` command had been issued. In other words, the sequence of `RSET` followed immediately by `EHLO` is redundant, but not harmful other than in the performance cost of executing unnecessary commands.

### `MAIL`

### `MAIL` example

```
C: MAIL FROM:<bob@example.org>S: 250 Requested mail action okay completed
```

### `MAIL` request

The mail request.

This command is used to initiate a mail transaction in which the mail data is delivered to an SMTP server. The argument field contains a source mailbox address (between “<” and “>” brackets).

This command clears the source buffer, the destination buffer, and the mail data buffer; and inserts the source information from this command into the source buffer.

Log example:

```
C: MAIL FROM:<bob@example.org>
```

In ABNF syntax,

```
mail-request                = "MAIL FROM:" "<" Source ">" CRLFSource                      = MailboxMailbox                     = Dot-string "@" DomainDomain                      = (sub-domain 1*("." sub-domain)) / address-literalsub-domain                  = Let-dig [Ldh-str]address-literal             = "[" IPv4-address-literal "]"Dot-string                  = Atom *("." Atom)Atom                        = Let-dig *(Let-dig / "-")
```

### `MAIL` response

The mail response.

The server will give either a successful response, or an error response. The server will send a `503-response` if the client is calling at a wrong state. See section “`SMTP-CRAM` state diagrams” for more information. If `Source` is invalid, the server reports a `501-response`.

If `Source` is valid, the server always returns a `250` reply.

Log example:

```
S: 250 Requested mail action okay completed
```

In ABNF syntax,

```
mail-ok-response            =   "250" SP "Requested mail action okay completed"                                CRLF
```

### `RCPT`

### `RCPT` example

```
C: RCPT TO:<bob@example.org>S: 250 Requested mail action okay completed
```

### `RCPT` request

The recipient request.

This command is used to identify an individual recipient of the mail data; multiple recipients are specified by multiple uses of this command.

This command inserts the destination information from this command into the destination buffer.

Log example:

```
C: RCPT TO:<bob@example.org>
```

In ABNF syntax,

```
rcpt-request                = "RCPT TO:" "<" Destination ">" CRLFDestination                 = MailboxMailbox                     = Dot-string "@" DomainDomain                      = (sub-domain 1*("." sub-domain)) / address-literalsub-domain                  = Let-dig [Ldh-str]address-literal             = "[" IPv4-address-literal "]"Dot-string                  = Atom *("." Atom)Atom                        = Let-dig *(Let-dig / "-")
```

### `RCPT` response

The recipient response.

The server will give either a successful response, or an error response. The server will send a `503-response` if the client is calling at a wrong state. See section “`SMTP-CRAM` state diagrams” for more information. If `Destination` is invalid, the server reports a `501-response`.

If `Destination` is valid, the server always returns a `250` reply.

Log example:

```
S: 250 Requested mail action okay completed
```

In ABNF syntax,

```
rcpt-ok-response            =   "250" SP "Requested mail action okay completed"                                CRLF
```

### `DATA`

### `DATA` example

```
C: DATAS: 354 Start mail input end <CRLF>.<CRLF>C: Never gonnaS: 354 Start mail input end <CRLF>.<CRLF>C:  give you upS: 354 Start mail input end <CRLF>.<CRLF>C: .S: 250 Requested mail action okay completed
```

### `DATA` request

The data request.

This command is used to send mail data continuously until the end of mail data indication.

The server normally sends a `354` response to the client, and then the server treats the lines (strings ending in `<CRLF>` sequences) following the command as mail data from the client. The mail data is terminated by a line containing only a period, that is, the character sequence `<CRLF>.<CRLF>`. This is the end of mail data indication.

Log example:

```
C: DATAC: Never gonna...C: give you upC: .
```

Note that the last client message should be exactly `<CRLF>.<CRLF>`.

In ABNF syntax,

```
data-request                = "DATA" CRLFline-data                   = *OCTET CRLFend-of-email                = CRLF "." CRLF
```

### `DATA` response

The data response.

The server will give either a successful response, an intermediate response or an error response. The server will send a `503-response` if the client is calling at a wrong state. See section “`SMTP-CRAM` state diagrams” for more information. The server will send a `501-response` if one or more parameters are specified.

Otherwise, the server always continuously returns a `354` reply, until the end of email indicator is received, then finally returns a `250` reply.

Log example:

```
S: 354 Start mail input end <CRLF>.<CRLF>S: 354 Start mail input end <CRLF>.<CRLF>S: 354 Start mail input end <CRLF>.<CRLF>S: 250 Requested mail action okay completed
```

In ABNF syntax,

```
data-int-response           =   "354" SP "Start mail input end <CRLF>.<CRLF>"                                CRLFdata-ok-response            =   "250" SP "Requested mail action okay completed"                                CRLF
```

### `RSET`

### `RSET` example

```
C: RSETS: 250 Requested mail action okay completed
```

### `RSET` request

The reset request.

This command specifies that the current mail transaction will be aborted. Any stored sender, recipients, and mail data MUST be discarded, and all buffers are cleared. A reset command may be issued by the client at any time.

Log example:

```
C: RSET
```

In ABNF syntax,

```
rset-request                = "RSET" CRLF
```

### `RSET` response

The reset response.

The server will give either a successful response, or an error response. The server will send a `501-response` if one or more parameters are specified.

Otherwise, the server MUST send a `250` reply to a RSET command with no arguments.

Log example:

```
S: 250 Requested mail action okay completed
```

In ABNF syntax,

```
rset-ok-response            =   "250" SP "Requested mail action okay completed"                                CRLF
```

### `NOOP`

### `NOOP` request

```
C: NOOPS: 250 Requested mail action okay completed
```

### `NOOP` request

The noop request.

This command does not affect any parameters, stored buffer or previously entered commands. It specifies no action other than that the receiver send an OK reply.

Log example:

```
C: NOOP
```

In ABNF syntax,

```
rset-request                = "NOOP" CRLF
```

### `NOOP` response

The reset response.

The server will give either a successful response, or an error response. The server will send a `501-response` if one or more parameters are specified.

Otherwise, the server MUST send a `250` reply to a `NOOP` command with no arguments.

Log example:

```
S: 250 Requested mail action okay completed
```

In ABNF syntax,

```
noop-ok-response            =   "250" SP "Requested mail action okay completed"                                CRLF
```

### `AUTH`

The authentication protocol exchange consists of a series of server challenges and client answers that are specific to the authentication mechanism.

### `CRAM-MD5` explanation

The server challenge is a presumptively arbitrary string.

The client answer is a string consisting of the user name, a space, and a digest. This is computed by applying the keyed MD5 algorithm from [RFC 2104 HMAC: Keyed-Hashing for Message Authentication](https://www.rfc-editor.org/rfc/rfc2104) where the key is a shared secret. This shared secret is a string known only to the client and server. When the server receives this client response, it verifies the digest provided. If the digest is correct, the server should consider the client authenticated and respond appropriately.

### `AUTH` request and response

The authenticate request and response.

The client will ask for a server challenge, then the server will give the challenge in an intermediate response. Then the client will send an answer to the challenge, and the server will give either a successful response or an error response.

The `AUTH` command indicates a SASL authentication mechanism to the server. In the scope of this assignment, only `CRAM-MD5` is implemented and can be accepted. Any other mechanism provided as an argument can be considered unsupported.

If the server supports the requested authentication mechanism (again, only `CRAM-MD5`), it performs an authentication protocol exchange to authenticate and identify the user. If the requested authentication mechanism is not supported, the server rejects the AUTH command with a `504` reply.

A server challenge is sent as a `334` reply with the first response parameter after code containing a BASE64 encoded string supplied by the SASL mechanism. The length of the server challenge needs to be greater than or equal to 16 bytes and less than or equal to 128 bytes. This challenge MUST NOT contain any data other than the BASE64 encoded challenge.

The client answer consists of a line containing a BASE64 encoded string. If the client wishes to cancel an authentication exchange, it issues a line with a single "*". If the server receives such an answer, it MUST reject the AUTH command by sending a `501` reply.

If the server cannot (BASE64) decode the argument, it rejects the AUTH command with a `501` reply. The server MUST reject invalid authentication answer data with a `535` reply. Should the client successfully complete the authentication exchange, the SMTP server issues a `235` reply.

The `AUTH` command is not permitted during a mail transaction. During a mail transaction, a server MUST reject any `AUTH` commands with a `503` reply. After an `AUTH` command has successfully completed, no more `AUTH` commands may be issued in the same session. After a successful `AUTH` command completes, a server MUST reject any further `AUTH` commands with a `503` reply.

In ABNF syntax,

```
auth-init-request           =   "AUTH" SP "CRAM-MD5" CRLFauth-int-response           =   "334" SP auth-challenge                                CRLFauth-challenge              =   *OCTETauth-client-answer          =   *OCTET CRLFauth-ok-response            =   "235" SP "Authentication successful"                                CRLF
```

Where `auth-challenge` is an abitrary long BASE64-encoded random string. It should not be static and not be shorter than 16 bytes.

In ABNF syntax, a successful authentication log example can be:

```
C: auth-init-requestS: auth-int-responseC: auth-challengeS: auth-ok-response
```

In ABNF syntax, an unsuccessful authentication log example can be:

```
C: "AUTH" SP "CRAM-MD55555555" CRLFS: 504-response
```

or

```
C: auth-init-requestS: auth-int-responseC: auth-challengeS: 535-response
```

### `QUIT`

### `QUIT` example

```
C: QUITS: 221 Service closing transmission channel
```

Note that the client is expected to disconnect ONLY after receiving `221`.

### `QUIT` request

The quit request.

This command specifies that the server MUST send an `OK` reply, and then close the transmission channel.

The client MUST NOT intentionally close the transmission channel until it sends a QUIT command and waits until it receives the `OK` reply, even if there was an error response to a previous command. The server MUST NOT intentionally close the transmission channel until it receives and replies to a valid `QUIT` command, even if there was an error caused by a previous command.

If the connection is closed prematurely due to violations of the above or system or network failure, the server MUST cancel any pending mail transaction, but not undo any previously completed transaction, and generally MUST act as if the command or transaction in progress had received a temporary error.

The `QUIT` command may be issued at any time.

Log example:

```
C: QUIT
```

In ABNF syntax,

```
rset-request                = "QUIT" CRLF
```

### `QUIT` response

The quit response.

The server will give either a successful response, or an error response. The server will response a `501-response` if one or more parameters are specified.

Otherwise, the server MUST send a `221` reply to a QUIT command with no arguments.

Log example:

```
S: 221 Service closing transmission channel
```

In ABNF syntax,

```
rset-ok-response            =   "250" SP "Service closing transmission channel"                                CRLF
```