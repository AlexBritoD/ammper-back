import httpx
import base64
from typing import List, Dict, Any
from app.core.config import settings

class BelvoClient:
    def __init__(self):
        self.base_url = settings.BELVO_BASE_URL
        self.secret_id = settings.BELVO_SECRET_ID
        self.secret_password = settings.BELVO_SECRET_PASSWORD
        
        # Create basic auth header
        credentials = f"{self.secret_id}:{self.secret_password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json"
        }

    async def get_institutions(self) -> List[Dict[str, Any]]:
        """Get all available institutions (banks)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/institutions/?country_code__in=BR,MX",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    async def create_link(self, institution: str, username: str, password: str, username2: str = None) -> Dict[str, Any]:
        """Create a link to a financial institution."""
        payload = {
            "institution": institution,
            "username": username,
            "password": password,
        }
        
        if username2:
            payload["username2"] = username2
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/links/",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def get_accounts(self, link_id: str = None) -> List[Dict[str, Any]]:
        """Get accounts from Belvo."""
        params = {}
        if link_id:
            params["link"] = link_id
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/accounts/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    async def get_account_by_id(self, account_id: str) -> Dict[str, Any]:
        """Get a specific account by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/accounts/{account_id}/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_transactions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get transactions for a specific account."""
        params = {"account": account_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/transactions/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    async def create_demo_link(self) -> Dict[str, Any]:
        """Create a demo link for testing purposes."""
        return await self.create_link(
            institution="erebor_mx_retail",
            username="testuser",
            password="testpass"
        )

# Singleton instance
belvo_client = BelvoClient()