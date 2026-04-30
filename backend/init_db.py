from database import engine, Base
import models  # noqa: F401 – テーブル定義をすべてインポートしてから create_all


def init_db():
    Base.metadata.create_all(bind=engine)
    print("All tables created.")


if __name__ == "__main__":
    init_db()
