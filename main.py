import socketserver
from gitlabServerHook import MyHandler

IP = "172.20.16.21"
PORT = 13140

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        Handler = MyHandler
        with socketserver.TCPServer((IP, PORT), Handler) as httpd:
            print(f"Starting http://{IP}:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping by Ctrl+C")
        httpd.server_close()  # to resolve problem `OSError: [Errno 98] Address already in use`
