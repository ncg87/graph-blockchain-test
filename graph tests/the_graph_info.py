import requests

def get_types_query():
    """
    Introspection query to fetch all available types in the schema
    """
    return """
    query {
        __schema {
            types {
                name
                kind
                description
            }
        }
    }
    """

def get_schema_query():
    """
    Introspection query to fetch all available fields for different types
    """
    return """
    query {
        __schema {
            types {
                name
                kind
                fields {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
def list_schema_types(url):
    response = requests.post(url, json={
        "query": get_types_query()
    })
    
    # Parse the response
    schema_data = response.json()
    
    # Categorize and print types
    print("Schema Types:")
    print("\nObject Types:")
    for type_info in schema_data['data']['__schema']['types']:
        if type_info['kind'] == 'OBJECT':
            print(f"- {type_info['name']}")
    
    print("\nEnum Types:")
    for type_info in schema_data['data']['__schema']['types']:
        if type_info['kind'] == 'ENUM':
            print(f"- {type_info['name']}")
    
    print("\nInput Types:")
    for type_info in schema_data['data']['__schema']['types']:
        if type_info['kind'] == 'INPUT_OBJECT':
            print(f"- {type_info['name']}")
    
    print("\nScalar Types:")
    for type_info in schema_data['data']['__schema']['types']:
        if type_info['kind'] == 'SCALAR':
            print(f"- {type_info['name']}")
            
def explore_schema(url, interesting_types):
    response = requests.post(url, json={
        "query": get_schema_query()
    })
    
    # Parse and print out the schema
    schema_data = response.json()
    
    for type_info in schema_data['data']['__schema']['types']:
        print(f"\n{type_info['name']} Fields:")
        if type_info['name'] in interesting_types:
            for field in type_info['fields']:
                print(f"- {field['name']}: {field['type']['name']} ({field['type']['kind']})")