import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(                                                                                                          
    "DATABASE_URL",                                                                                                                
    "mysql+pymysql://root:password@localhost:3306/policy_desk_db"                                                                  
)

# pool_pre_ping checks if connection is alive before handing it to a request
engine = create_engine(DATABASE_URL, pool_pre_ping=True)  

# SessionLocal is a factory that generates new database sessions                                                                   
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy models                                                                                             
Base = declarative_base()


def get_db():                                                                                                                      
    """                                                                                                                            
    FastAPI dependency that provides a transactional database session per request.                                                 
    Automatically closes the session when the request finishes (like Express middleware).                                          
    """                                                                                                                            
    db = SessionLocal()                                                                                                            
    try:                                                                                                                           
        yield db                                                                                                                   
    finally:                                                                                                                       
        db.close()