from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os

def init_cosmos_client():
    url = os.getenv("COSMOS_DB_URL")
    key = os.getenv("COSMOS_DB_PRIMARY_KEY")
    return CosmosClient(url, credential=key)
    
def get_database(client, database_name="UserDatabase"):
    return client.create_database_if_not_exists(id=database_name)
    
def get_container(database, container_name, partition_key):
    return database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path=partition_key)
    )
    
def get_cosmos_resources(container_name, partition_key="/id"):
    client = init_cosmos_client()
    database = get_database(client)
    return get_container(database, container_name, partition_key)
    
def save_user_info(user_info):
    try:
        container = get_cosmos_resources("UserInfo")
        container.upsert_item(user_info)
        return {"status": "success", "message": "User info saved successfully"}
    except exceptions.CosmosHttpResponseError as e:
        return {"status": "error", "message": str(e)}
        
def save_user_emails(user_emails, user_id):
    try:
        container = get_cosmos_resources("UserEmails")
        emails = [{"id": email["id"], "user_id": user_id, **email} for email in user_emails.get("value", [])]
        for email in emails:
            container.upsert_item(email)
        return {"status": "success", "message": "All user emails saved successfully"}
    except exceptions.CosmosHttpResponseError as e:
        return {"status": "error", "message": str(e)}
        
def get_emails(user_id):
    try:
        container = get_cosmos_resources("UserEmails")
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        items = list(container.query_items(query=query, parameters=[{"name": "@user_id", "value": user_id}], enable_cross_partition_query=True))
        return {"emails": items}
    except exceptions.CosmosHttpResponseError as e:
        return {"status": "error", "message": str(e)}
        
def save_access_token(user_id, access_token, expires_in=3600):
    try:
        container = get_cosmos_resources("UserToken")
        item = {
            "id": user_id,
            "user_id": user_id,
            "access_token": access_token,
            "expires_at": expires_in
        }
        container.upsert_item(item)
        return {"status": "success", "message": "Access token saved"}
    except exceptions.CosmosHttpResponseError as e:
        return {"status": "error", "message": str(e)}
        
def retrieve_access_token(user_id):
    try:
        container = get_cosmos_resources("UserToken")
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        items = list(container.query_items(query=query, parameters=[{"name": "@user_id", "value": user_id}], enable_cross_partition_query=True))
        return items[0]["access_token"] if items else None
    except exceptions.CosmosHttpResponseError as e:
        return None
        
def delete_access_token(user_id):
    try:
        container = get_cosmos_resources("UserToken")
        container.delete_item(user_id, partition_key=user_id)
        return {"status": "success", "message": "Token deleted"}
    except exceptions.CosmosResourceNotFoundError:
        return {"status": "error", "message": "Token not found"}
    except exceptions.CosmosHttpResponseError as e:
        return {"status": "error", "message": str(e)}
