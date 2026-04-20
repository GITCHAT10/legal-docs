from sqlalchemy import Column, Integer, String, Date

from mnos.core.db.base_class import Base
class Guest(Base):
    __tablename__ = "guest"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    passport_number = Column(String)
    nationality = Column(String)
    date_of_birth = Column(Date)
