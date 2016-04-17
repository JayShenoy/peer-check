from sqlalchemy import Column, ForeignKey, Integer, String, CHAR, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import hashlib
import random, string

from flask.ext.login import UserMixin

Base = declarative_base()

class User(Base, UserMixin):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(50), nullable=False)
	email = Column(String(50), nullable=False)
	password = Column(Text, nullable=False)
	salt = Column(String(50), nullable=False)
	school = Column(String(50), nullable=False)

	def check_password_hash(self, form_password):
		h = hashlib.sha512(self.salt + form_password)
		return self.password == h.hexdigest()

	def get_id(self):
		return unicode(self.id)

if __name__ == '__main__':
    engine = create_engine('sqlite:///data.db', echo=False)
    Base.metadata.create_all(engine)