from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app import models, schemas, crud, belvo_client, auth
from app.database import engine, get_db
from app.config import settings
from fastapi.responses import JSONResponse

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PWA Belvo Integration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = crud.create_user(db, user_in.username, user_in.password)
    return user

@app.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth.create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/banks")
def list_banks(page: int = 1, db: Session = Depends(get_db), current_user = Depends(auth.get_current_user)):
    data = belvo_client.list_institutions(page=page, db=db)
    return data

@app.get("/bank/{bank_id}/accounts")
def bank_accounts(bank_id: str, current_user = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    data = belvo_client.get_accounts_for_institution(bank_id, db)
    return data

@app.get("/account/{account_id}/kpis/{bank_name}")
def account_kpis(account_id: str, bank_name: str, current_user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    link_id = belvo_client.get_link_by_bank(bank_name, db)
    return belvo_client.get_account_kpis(account_id, link_id)


@app.post("/logout")
def logout(current_user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    crud.delete_user_session(db, current_user.id)
    return JSONResponse({"message": "Logout successful"})