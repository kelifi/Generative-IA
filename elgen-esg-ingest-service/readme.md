# Very useful ES queries!

```
GET _cluster/health

GET /_cat/nodes?v

GET /_cat/indices?v&expand_wildcards=all

PUT /products
{
  "settings":{
    "number_of_shards":2,
    "number_of_replicas":2
  }
}

DELETE /products

POST /products/_doc
{
  "name":"yeeah",
  "price":64
}

GET /products/_doc/K0kEJ4kBd4t-QExJoyRv

POST /products/_bulk
{ "index": { "_id": "1" }}
{ "field1": "value1", "field2": "value2" }
{ "index": { "_id": "2" }}
{ "field1": "value3", "field2": "value4" }
{ "index": { "_id": "3" }}
{ "field1": "value5", "field2": "value6" }

GET _ingest/pipeline
```