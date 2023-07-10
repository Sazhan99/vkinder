# импорты
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from vkinder.config import db_url_object


# схема БД
metadata = MetaData()
Base = declarative_base()


class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)

class Last_offset(Base):
    __tablename__ = 'last_offset'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    offset = sq.Column(sq.Integer, primary_key=True)


def add_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_bd)
        session.commit()

def last_offset(engine, profile_id, offset):
    with Session(engine) as session:
        to_bd = Last_offset(profile_id=profile_id, offset=offset)
        session.add(to_bd)
        session.commit()

def user_exists_in_db(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        # Запрос наличия пользователя в БД
        user = session.query(Viewed).filter(
            Viewed.profile_id == profile_id,
            Viewed.worksheet_id == worksheet_id).first()
        return True if user else False

# def set_offset(engine, profile_id, new_offset):
#     print(profile_id, new_offset)
#     with Session(engine) as session:
#         existing_offset = session.query(Last_offset).filter_by(profile_id=profile_id).first()
#         if existing_offset:
#             existing_offset.offset = new_offset
#         else:
#             new_entry = Last_offset(profile_id=profile_id, offset=new_offset)
#             session.add(new_entry)
#             session.commit()

def set_offset(engine, profile_id, new_offset):
    print(profile_id, new_offset)
    session = Session(engine)  # явное открытие сессии
    existing_offset = session.query(Last_offset).filter_by(profile_id=profile_id).first()
    if existing_offset:
        existing_offset.offset = new_offset
    else:
        new_entry = Last_offset(profile_id=profile_id, offset=new_offset)
        session.add(new_entry)

    session.commit()  # сохранение изменений в БД
    session.close()  # явное закрытие сессии


if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    # add_user(engine, 294898234, 87324234)
    # res = user_exists_in_db(engine, 294898234, 873242234)
    # pes = last_offset(engine, 301668832)
    # print(pes)

