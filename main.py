from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pymongo import MongoClient
from bson import json_util,objectid
from categories import Categories
from routes import route_function

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def _set_response(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    # def do_GET(self):
    #     if self.path == '/api/data':
    #         self._set_response()
    #         try:
    #             # Query data from MongoDB collection where id equals 1
    #             data = list(self.collection.find({'id': "563777"}))
    #             # Convert ObjectId fields to strings
    #             for item in data:
    #                 if '_id' in item:
    #                     item['_id'] = str(item['_id'])
    #             # Serialize data to JSON
    #             json_data = json_util.dumps(data)
    #             self.wfile.write(json_data.encode())
    #         except Exception as e:
    #             self._set_response(status_code=500)
    #             error_message = {'error': str(e)}
    #             self.wfile.write(json_util.dumps(error_message).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_data = post_data.decode('utf-8')
        post_data = json.loads(post_data)
        response_data = route_function(post_data,self.path)
        self._set_response(status_code=response_data['statusCode'])
        self.wfile.write(json_util.dumps(response_data).encode())

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()