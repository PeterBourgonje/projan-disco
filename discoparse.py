import requests
import json

"""
This assumes a container for discopy (https://github.com/rknaebel/discopy) to be running at localhost:8080:
docker run -it --rm  -p 8080:8080 rknaebel/discopy:1.0
"""

class Discopy:

    def __init__(self):
        self.url = "http://localhost:8080/api/parser"
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def parse(self, txt):
        data = json.dumps({'text': txt})
        try:
            response = requests.request("POST", self.url, headers=self.headers, data=data)
            return response.text
        except Exception as e:
            return str(e)
        
def main():
    dp = Discopy()
    result = dp.parse('I am going out , because the weather is good .')
    print(result)
        
if __name__ == '__main__':
    main()
