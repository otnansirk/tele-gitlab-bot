import os
from supabase import create_client, Client

class Database:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def insert(self, table_name: str, data: dict):
        return (
            self.supabase.table(table_name)
                .insert(data)
                .execute()
        )

    def fetch(self, table_name: str) -> Client: 
        return self.supabase.table(table_name)
