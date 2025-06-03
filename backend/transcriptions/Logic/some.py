from elasticsearch import Elasticsearch
from elasticsearch.exceptions import BadRequestError

try:
    es.index(index="my_index", document={"your": "data"})
except BadRequestError as e:
    print("Status code:", e.status_code)
    print("Error message:", e.error)
    print("Body:", e.info)  # Often shows the cause
