from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str


users = [
    {
        "id": 1,
        "name": "Ana",
        "email": "ana@example.com"
    },
    {
        "id": 2,
        "name": "Juan",
        "email": "juan@example.com"
    },
]
 

@app.get("/")
def root():
    return {"message": "Mi Primer API REST"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/users")
def get_all_users(limit: int =10):
    return users[:limit]

@app.get("/users/{user_id}")
def get_users(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado",
    )

@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "email": user.email
    }

    users.append(new_user)

    return new_user