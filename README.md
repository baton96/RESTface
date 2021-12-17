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

# TODO:

- Add filesystem-storage
- Setting / Validating schemas
- Autogenerating Swagger/OpenAPI specs
- **Example app using RESTface**
- Customizable path/url of storage
- Allowing UUID instead of integer ids
- Sorting by multiple criteria
- Multiple operations with same parameter name

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
