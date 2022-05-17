# 😴 RESTface 😴

RESTface is a Python tool that provides minimal viable REST API

## Installation

```pip install restface```

## Usage

```
restface [-h] -p PORT -h HOST -d DEBUG

Run restface server

positional arguments:
  arg1                  first argument

optional arguments:
  -h, --help                show this help message and exit
  
  -h HOST, --host HOST      hostname to listen on, set to '0.0.0.0' to have the server available externally as well, defaults to '127.0.0.1'
  
  -p PORT, --port PORT      port of the webserver, defaults to 5000
  
  -d DEBUG, --debug DEBUG   if given, enable or disable debug mode
```

# Storage types

- `DbStorage` - Any type of database supported by sqlalchemy
  (SQLite, Postgresql, MySQL, Oracle, MS-SQL, Firebird, Sybase); defaults to `sqlite:///:memory:`
- `FileStorage` - JSON file storage; defaults to virtual file ie. in-memory storage
- `MemoryStorage` - In-memory storage built from scratch
- `MongoStorage` - Defaults to `mongodb://localhost:27017`
- `RedisStorage` - Defaults to `redis://localhost:6379/0`
- `Neo4jStorage` - Defaults to `bolt://localhost:7687`

# Ideas:

- Neo4jStorage
- Setting schemas
- Validating schemas
- Autogenerating Swagger/OpenAPI specs
- **Example app using RESTface**
- Multiple operations with same parameter name
- Insert many

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
