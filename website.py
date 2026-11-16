from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

HOST = "localhost"
PORT = 8000

# Runs a local webb server.

def website_start():

    server = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
    print(f"Server running at http://{HOST}:{PORT}")

    try:
        webbrowser.open(f"http://{HOST}:{PORT}/web-interface/index.html")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()







# Test
def main():
    website_start()

if __name__ == "__main__":
    main()
