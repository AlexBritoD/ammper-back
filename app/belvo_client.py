import requests
from requests.auth import HTTPBasicAuth
from app.config import settings
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app import models
import json
from fastapi import HTTPException
import re
import rstr

from app.database import engine, get_db

auth = HTTPBasicAuth(settings.BELVO_CLIENT_ID, settings.BELVO_SECRET)
BASE = settings.BELVO_BASE_URL.rstrip("/")

def list_institutions(page: int = 1, per_page: int = 50, db: Optional[Session] = None) -> Dict[str, Any]:
    if db is None:
        db = next(get_db()) 
    url = f"{BASE}/institutions/"
    params = {"page": page, "page_size": per_page}
    r = requests.get(url, auth=auth, params=params, timeout=15)
    r.raise_for_status()

    institutions = r.json()
    results = institutions.get("results", institutions)

    try:
        for inst in results:
            existing = db.query(models.Institution).filter(models.Institution.id == str(inst["id"])).first()
            if existing:
                for key, value in inst.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                db.add(models.Institution(**{k: v for k, v in inst.items() if hasattr(models.Institution, k)}))

        db.commit()
    finally:
        db.close()

    return institutions

def get_institution(institution_id: str) -> Dict[str, Any]:
    url = f"{BASE}/institutions/{institution_id}/"
    r = requests.get(url, auth=auth, timeout=15)
    r.raise_for_status()
    return r.json()

def get_accounts_for_institution(institution_id: str, db: Session) -> Dict[str, Any]:
    try:
        institution = register_link_institution(institution_id, db)
    except HTTPException as e:
        raise e

    url = f"{BASE}/accounts/?link={institution['id']}"
    try:
        r = requests.get(url, auth=auth, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError:
        try:
            error_data = r.json()
        except Exception:
            error_data = {"detail": "Error desconocido al obtener cuentas"}
        raise HTTPException(status_code=r.status_code, detail=error_data)


def register_link_institution(institution_id: str, db: Session) -> Dict[str, Any]:
    institution = db.query(models.Institution).filter(models.Institution.name == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institución no encontrada en la base de datos")

    existing_link: Optional[models.Link] = (
        db.query(models.Link).filter(models.Link.institution == institution.name).first()
    )
    if existing_link and existing_link.status == "valid":
        return {
            "id": existing_link.id,
            "institution": existing_link.institution,
            "status": existing_link.status,
            "fetch_resources": existing_link.fetch_resources,
        }

    form_fields = institution.form_fields or []
    credentials = {}
    for field in form_fields:
        name = field["name"]
        pattern = field.get("validation")
        credentials[name] = rstr.xeger(pattern) if pattern else "test123"
        if field['type'] == 'select':
            if institution.name == 'ofmockbank_br_retail':
                credentials[name] = "103"
            credentials[name] = "003"

    if institution.name == 'ofmockbank_br_retail':
        credentials['username_type'] = "103"
    payload = {
        "institution": institution.name,
        "fetch_resources": institution.resources or ["ACCOUNTS", "TRANSACTIONS", "BALANCES"],
        **credentials,
    }
    print(payload)

    url = f"{BASE}/links/"
    try:
        r = requests.post(url, auth=auth, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError:
        
        try:
            error_data = r.json()
        except Exception:
            error_data = {"detail": "Error desconocido al registrar el link"}
        raise HTTPException(status_code=r.status_code, detail=error_data)

    if existing_link:
        existing_link.id = data["id"]
        existing_link.status = data["status"]
        existing_link.fetch_resources = data["fetch_resources"]
    else:
        new_link = models.Link(
            id=data["id"],
            institution=data["institution"],
            status=data["status"],
            fetch_resources=data["fetch_resources"],
        )
        db.add(new_link)

    db.commit()
    return data

def get_link_by_bank(bank_name: str, db: Session) -> str:
    
    link_entry: models.Link = db.query(models.Link).filter(models.Link.institution == bank_name).first()
    if not link_entry:
        raise HTTPException(status_code=404, detail=f"No se encontró un link para el banco {bank_name}")
    return link_entry.id


def get_account_kpis(account_id: str, link_id: str) -> Dict:
    url = f"{BASE}/transactions/"
    params = {"account": account_id, "link": link_id, "page_size": 200}
    r = requests.get(url, auth=HTTPBasicAuth(settings.BELVO_CLIENT_ID, settings.BELVO_SECRET), params=params, timeout=15)

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())

    data = r.json()
    txs = data.get("results", [])

    ingresos = sum(t["amount"] for t in txs if t.get("type") == "INFLOW" and t.get("status") == "PROCESSED")
    ingresos_pendientes = sum(t["amount"] for t in txs if t.get("type") == "INFLOW" and t.get("status") == "PENDING")
    egresos = sum(abs(t["amount"]) for t in txs if t.get("type") == "OUTFLOW" and t.get("status") == "PROCESSED")
    egresos_pendientes = sum(abs(t["amount"]) for t in txs if t.get("type") == "OUTFLOW" and t.get("status") == "PENDING")

    balance = ingresos - egresos
    account_currency = txs[0]["account"]["currency"] if txs else None

    return {
        "balance": balance,
        "ingresos": ingresos,
        "ingresos_pendientes": ingresos_pendientes,
        "egresos": egresos,
        "egresos_pendientes": egresos_pendientes,
        "account_currency": account_currency,
        "transactions": txs
    }

