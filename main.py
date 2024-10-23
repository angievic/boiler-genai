from fastapi import Depends, FastAPI,HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session
from database import create_db_and_tables, get_session
from models import PersonDataRequest
import crud
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Hola, mundo!"}

@app.post("/create-person")
async def create_person(
    request: PersonDataRequest,
    session: Session = Depends(get_session)
):
    try:
        # Save the information in the database
        new_person = crud.create_person(
            session=session,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name
        )
        print("before generate")
        print(new_person)
        return JSONResponse(status_code=200, content={"message": "Person created"})
    except Exception as e:
        print(e,"error in exception")
        raise HTTPException(status_code=500, detail=str(e))

