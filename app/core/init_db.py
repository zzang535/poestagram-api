from app.core.database import engine
from app.models import user

def init_db():
    user.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db() 