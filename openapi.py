from copy import deepcopy
from sqlalchemy import Integer, UnicodeText, BigInteger, Float, Boolean  # type: ignore[import-untyped]

type_map = {
    Integer: "integer",
    UnicodeText: "string",
    BigInteger: "integer",
    Float: "number",
    Boolean: "boolean",
}

id_parameter = {
    "name": "id",
    "in": "path",
    "required": True,
    "schema": {
        "oneOf": [
            {"type": "string", "format": "uuid"},
            {"type": "integer"},
        ]
    },
}


def get_schema(db, engine):
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "RESTface API",
            "version": "1.0.0",
        },
        "paths": [],
        "tags": [],
    }
    paths = {}
    for table_name in db.tables:
        properties = {}
        obj_parameters = []
        item_name = engine.singular_noun(table_name)
        schema["tags"] += [{"name": table_name.capitalize()}]
        for column in db.get_table(table_name)._table.columns:
            column_name = str(column.name)
            openapi_type = type_map[type(column.type)]
            properties[column_name] = {"type": openapi_type}
            obj_parameters += [
                {"name": column_name, "in": "query", "schema": openapi_type}
            ]

        paths[f"/{table_name}"] = {
            "get": {
                "description": f"Get a list of {table_name}",
                "summary": f"Get a list of {table_name}",
                "parameters": obj_parameters,
                "tags": [table_name.capitalize()],
                "responses": {
                    "200": {
                        "description": f"A list of {table_name}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": properties,
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "description": f"Add new {item_name}",
                "summary": f"Add new {item_name}",
                "parameters": obj_parameters,
                "tags": [table_name.capitalize()],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": f"ID of {item_name}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "oneOf": [
                                        {"type": "string", "format": "uuid"},
                                        {"type": "integer"},
                                    ]
                                }
                            }
                        },
                    },
                },
            },
            "delete": {
                "description": f"Delete {table_name}",
                "summary": f"Delete {table_name}",
                "parameters": obj_parameters,
                "tags": [table_name.capitalize()],
                "responses": {
                    "204": {"description": f"{item_name.capitalize()} deleted"}
                },
            },
        }

        paths[f"/{table_name}/{{id}}"] = {
            "get": {
                "description": f"Get {item_name} by id",
                "summary": f"Get {item_name} by id",
                "parameters": [id_parameter],
                "tags": [table_name.capitalize()],
                "responses": {
                    "200": {
                        "description": f"An object representing {item_name}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": properties,
                                }
                            }
                        },
                    },
                    "404": {
                        "description": f"{item_name.capitalize()} not found",
                    },
                },
            },
            "post": deepcopy(paths[f"/{table_name}"]["post"]),
            "delete": deepcopy(paths[f"/{table_name}"]["delete"]),
        }
        paths[f"/{table_name}/{{id}}"]["post"]["parameters"][0] = id_parameter
        paths[f"/{table_name}/{{id}}"]["delete"]["parameters"] = [id_parameter]
    schema["paths"] = paths
    return schema
