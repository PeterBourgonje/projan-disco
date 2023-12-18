import requests
import json
import sys

"""
This assumes a container for discopy (https://github.com/rknaebel/discopy) to be running at localhost:8080:
docker pull rknaebel/discopy:1.0.2
docker run -it --rm  -p 8080:8080 rknaebel/discopy:1.0.2
"""

DISCOPY_BATCH_SIZE_SENTENCES = 300


def batch(inp, batch_size):
    lst = len(inp)
    for ndx in range(0, lst, batch_size):
        yield inp[ndx:min(ndx + batch_size, lst)]


class Discopy:

    def __init__(self):
        self.url = "http://localhost:1133/api/parser/tokens"
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # checking if the parser is running:
        test_input = {'sentences': ['If I could offer maintenance of fantasies I would .'.split()]}
        try:
            response = requests.request("POST", self.url, headers=self.headers, data=json.dumps(test_input))
            assert response.status_code == 200
        except requests.exceptions.ConnectionError as e:
            sys.stderr.write("\nERROR: Discopy not found. Are you sure a container is running at '%s'?\n\n" % self.url)
            sys.exit()

    def parse(self, sentences):
        data = json.dumps({'sentences': sentences})
        print(f"data: {data}")

        final_response = {'docID': None,
                          'meta': None,
                          'text': '',
                          'sentences': [],
                          'relations': []
                          }

        try:
            # ran out of memory for longer texts, so doing batch-wise parsing here. This is very rudimentary, and just
            # cuts up the sentences into batches as if it were separate texts. TODO: implement overlapping batches..
            # Implies dealing with merging potentially conflicting information for the same input.
            char_offset = 0
            token_offset = 0
            for b in batch(sentences, DISCOPY_BATCH_SIZE_SENTENCES):
                data = json.dumps({'sentences': b})
                response = requests.request("POST", self.url, headers=self.headers, data=data)
                jr = json.loads(response.text)
                final_response['docID'] = jr['docID']
                final_response['meta'] = jr['meta']
                final_response['text'] += jr['text']
                final_response['sentences'] += jr['sentences']
                relations = jr['relations']
                for rel in relations:
                    for elem in rel:
                        if isinstance(rel[elem], dict) and 'TokenList' in rel[elem]:
                            rel[elem]['TokenList'] = [x + token_offset for x in rel[elem]['TokenList']]
                            cpl = rel[elem]['CharacterSpanList']
                            for i, span in enumerate(cpl):
                                span = [x + char_offset for x in span]
                                cpl[i] = span
                            # TODO: There seems to be some weird stuff going on, with r2l character spans like [71, 5]
                char_offset += len(jr['text'])
                token_offset += sum(len(x) for x in b)
                final_response['relations'] += relations
            assert len(sentences) == len(final_response['sentences'])
            return json.dumps(final_response)
        except Exception as e:
            return str(e)
        
def main():
    dp = Discopy()
    result = dp.parse(['I am going out.'.split(), 'Because the weather is good .'.split()])
    result = dp.parse(["There's smoke in my iris.".split(), "But I painted a sunny day on the inside of my eyelids.".split()])
    print(result)
        
if __name__ == '__main__':
    main()
