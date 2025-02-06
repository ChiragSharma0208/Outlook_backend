import requests

def get_access_token(client_id, client_secret, redirect_uri, code):
    """Exchange authorization code for access token"""
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    

    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        if response.json().get('error') == 'invalid_grant':
            error_description = response.json().get('error_description')
            if "The code has expired" in error_description:
                print("Authorization code has expired. Please ask the user to reauthorize.")
                return None
        
        print(f"Error: {response.status_code}")
        print(f"Response Text: {response.text}")
        return None
    print("Error response from Microsoft OAuth2:", response.text)
    response.raise_for_status()  
    return response.json()


def get_user_info(access_token):
    """Fetch user information from Microsoft Graph API using access token"""
    user_info_url = "https://graph.microsoft.com/v1.0/me"
    
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    

    response = requests.get(user_info_url, headers=headers)
    response.raise_for_status()  

    return response.json()

def get_user_emails(access_token): 
    """Fetch user emails from Microsoft Graph API using access token"""
    user_emails_url = "https://graph.microsoft.com/v1.0/me/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(user_emails_url, headers=headers)
    response.raise_for_status()  
    return response.json()  