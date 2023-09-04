import requests
import json
import sys

"""
This assumes a container for discopy (https://github.com/rknaebel/discopy) to be running at localhost:8080:
docker run -it --rm  -p 8080:8080 rknaebel/discopy:1.0
"""

class Discopy:

    def __init__(self):
        self.url = "http://localhost:8080/api/parser/tokens"
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # checking if the parser is running:
        test_input = {'sentences': ['If I could offer maintenance to fantasies I would .'.split()]}
        try:
            response = requests.request("POST", self.url, headers=self.headers, data=json.dumps(test_input))
            assert response.status_code == 200
        except Exception as e:
            sys.stderr.write("\nERROR: Discopy not found. Are you sure a container is running at '%s'?\n\n" % self.url)

    def parse(self, sentences):
        data = json.dumps({'sentences': sentences})
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
