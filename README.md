# 😴 RESTface 😴

RESTface is a Python tool that provides minimal viable REST API

## Installation

```pip install restface```

## Usage

```
restface [-help] [--port PORT] [-host HOST]

Run RESTface server

optional arguments:
  --help                show this help message and exit
  --host HOST      hostname to listen on, set to '0.0.0.0' to have the server available externally as well, defaults to '127.0.0.1'
  --port PORT      port of the webserver, defaults to 5000
```

# Storage types

- `DbStorage` - any type of database supported by sqlalchemy
  (SQLite, Postgresql, MySQL, Oracle, MS-SQL, Firebird, Sybase); defaults to `sqlite:///:memory:`
- `FileStorage` - JSON file storage; defaults to virtual file ie. in-memory storage
- `MemoryStorage` - in-memory storage built from scratch
- `RedisStorage` - defaults to `redis://localhost:6379/0`
- ~~`MongoStorage`~~, defaults to `mongodb://localhost:27017`
- ~~`Neo4jStorage`~~, defaults to `bolt://localhost:7687`

# TODO:
- **Example app using RESTface**
- Persistent db dump
- Graph database storage
- FastAPI instead of Flask
