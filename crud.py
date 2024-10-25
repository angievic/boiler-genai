from sqlmodel import Session
from models import Person
from fastapi import HTTPException
from datetime import datetime

def create_person(session: Session, first_name: str, last_name: str, email: str):
    new_person = Person(
        timestamp=datetime.utcnow(),
        first_name=first_name,
        last_name=last_name,
        email=email
    )
    session.add(new_person)
    session.commit()
    session.refresh(new_person)
    return new_person

def read_person(session: Session, person_id: int):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="TablaPerson not found")
    return person

def update_person_email(session: Session, person_id: int, email: str):
    person = session.get(Person, person_id)
    if person:
        person.email = email
        session.add(person)
        session.commit()
        session.refresh(person)
    return person
