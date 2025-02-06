from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os

def init_cosmos_client():
    url = os.getenv("COSMOS_DB_URL")
    key = os.getenv("COSMOS_DB_PRIMARY_KEY")
    return CosmosClient(url, credential=key)

def get_or_create_database(client, database_name):
    try:
        return client.create_database_if_not_exists(id=database_name)
    except Exception as e:
        print(f"Error creating/retrieving database: {e}")
        raise

def get_or_create_container(database, container_name, partition_key):
    try:
        return database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key)
        )
    except Exception as e:
        print(f"Error creating/retrieving container: {e}")
        raise

def save_user_info(user_info):
    client = init_cosmos_client()
    database = get_or_create_database(client, "UserDatabase")
    container = get_or_create_container(database, "UserInfo", partition_key="/id")

    try:
        container.upsert_item(body=user_info)
        print("User info saved or updated successfully.")
    except Exception as e:
        print(f"Error saving user info: {e}")
        raise
    
def save_user_emails(user_emails,user_id):
    try:
        client = init_cosmos_client()
        database = get_or_create_database(client, "UserDatabase")
        container = get_or_create_container(database, "UserEmails", partition_key="/id")
           
        for email in user_emails.get("value", []):
            email["user_id"] = user_id
            container.upsert_item(body=email)  

        print("All user emails saved successfully.")
    except Exception as e:
        print(f"Error saving user emails: {e}")
        raise

def get_emails(user_id):
    try:
        client = init_cosmos_client()
        database = get_or_create_database(client, "UserDatabase")
        container = get_or_create_container(database, "UserEmails", partition_key="/id")

        query = f"SELECT * FROM c where c.user_id='{user_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))

        return ({"emails": items})
    except Exception as e:
        return ({"error": str(e)})
