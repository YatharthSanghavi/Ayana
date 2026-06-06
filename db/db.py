from supabase import create_client, Client
from dotenv import load_dotenv
from flask import session
import os

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_supabase() -> Client:
    """Creates a fresh Supabase client acting as the logged-in user."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    access_token = session.get("access_token")
    refresh_token = session.get("refresh_token")
    
    if access_token and refresh_token:
        client.auth.set_session(access_token, refresh_token)
        
    return client