from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr

app = FastAPI()

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


users = [
    {
        "id": 1,
        "name": "Ana",
        "email": "ana@example.com",
        "internal_notes": "Esta es una nota interna que no se debe exponer en la respuesta"
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

@app.get("/users", response_model=list[UserResponse])
def get_users(
    limit: int = Query(default=10, ge=1, le=100, description="Número máximo de usuarios a devolver")
):
    return users[:limit]

@app.get("/users/{user_id}", response_model=UserResponse)
def get_users(user_id: int):
    for user in users:
        if user["id"] == user_id:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado",
    )

@app.post(
        "/users",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "email": user.email
    }

    users.append(new_user)

    return new_user