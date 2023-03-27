from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from data_config import *

# Создание подключения к базе данных
engine = create_engine(f'{db_driver}://{user}:{password}@{host}:{port}/{db_name}')
# Создание сессии для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()
# Определение базовой модели
Base = declarative_base()


# Определение моделей таблиц

class ViewedUser(Base):
    __tablename__ = 'viewed_user'
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer)
    find_id = Column(Integer)
    vk_link = Column(String(50))

# Создание таблиц в базе данных

def create_tables():
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы")


def delete_all_tables(engine):
    meta = MetaData()
    meta.reflect(bind=engine)
    for table in reversed(meta.sorted_tables):
        table_obj = Table(table.name, meta, autoload=True, autoload_with=engine)
        table_obj.drop(engine)
    print("Таблицы успешно удалены")


def insert_viewed_user(vk_id, find_id, vk_link, ):
    # Создание нового встреченного пользователя
    new_seen_user = ViewedUser(vk_id=vk_id, find_id=find_id, vk_link=vk_link)
    # Добавление встреченного пользователя в базу данных
    session.merge(new_seen_user)
    session.commit()


def select_viewed_user(find_id, user_id):
    user_id = session.query(ViewedUser.find_id).filter_by(find_id=find_id, vk_id=user_id).first()
    if user_id is None:
        return None
    else:
        return int(user_id.find_id)
