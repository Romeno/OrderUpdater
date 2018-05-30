# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, BigInteger, Text, TIMESTAMP, text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from ou_common import get_child, to_bool

import datetime

Base = declarative_base()


# сайты
class Site(Base):
	__tablename__ = 'site'

	site_id = Column(Integer, nullable=False, primary_key=True)	# Ид
	name = Column(Text)											# сервер
	niche_id = Column(Integer)									# Ид ниши
	time_load = Column(TIMESTAMP, server_default=text('NOW()')) # время загрузки
	user_load = Column(Text)									# пользователь загрузки
	feed = Column(Text)
	filename = Column(Text) 									# НаименованиеФайла


# табличка с по заказу в целом
class LeadStore(Base):
	__tablename__ = 'lead_store'

	site_name = Column(Text)									# СайтНаименование
	id = Column(BigInteger, nullable=False, primary_key=True)	# ИД
	order_type = Column(Integer)								# ТипЗаказа
	time_create = Column(BigInteger)  							# ВремяСоздания (UTC)
	name = Column(Text)											# Имя
	email = Column(Text)  										# email
	phone = Column(Text)  										# телефон
	address = Column(Text)										# Адрес
	message = Column(Text) 										# КомментарийКлиента
	roistat = Column(Text)										# СлужебноеПоле\roistat
	utm = Column(Text)  										# СлужебноеПоле\utm
	utm2 = Column(Text)  										# СлужебноеПоле\utm2
	utm3 = Column(Text)  										# СлужебноеПоле\utm3
	utm4 = Column(Text)  										# СлужебноеПоле\utm4
	utm5 = Column(Text)  										# СлужебноеПоле\utm5
	time_load = Column(TIMESTAMP, server_default=text('NOW()')) # время загрузки
	user_load = Column(Text)
	ip = Column(Text)  											# IpПользователя


# табличка с по заказу в каждому предмету в заказе
class LeadOrderItems(Base):
	__tablename__ = 'lead_order_items'

	item_id = Column(BigInteger, nullable=False, primary_key=True)	# ИД
	site_name = Column(Text)									# СайтНаименование
	id = Column(BigInteger)										# ИД заказа
	name = Column(Text)											# Наименование
	code = Column(Text)											# артикул
	param = Column(Text)										# размер
	qty = Column(Integer) 										# количество
	price = Column(Numeric)										# цена
	time_load = Column(TIMESTAMP, server_default=text('NOW()')) # время загрузки
	user_load = Column(Text)


engine = None
DBSession = None
session = None


def connect(db_username, db_password, db_host, db_name):
	global engine
	global DBSession
	global session

	engine = create_engine('postgresql://{}:{}@{}/{}'.format(db_username, db_password, db_host, db_name))

	Base.metadata.bind = engine

	DBSession = sessionmaker(bind=engine)

	session = DBSession()


def create_db():
	Base.metadata.create_all(engine)


def get_sites():
	return session.query(Site).all()


def get_last_order_id(site):
	order = session.query(LeadStore)\
		.filter_by(site_name=site.name)\
		.order_by(desc(LeadStore.id))\
		.first()

	if order:
		return order.id
	else:
		return 0


def store_order(site, order):
	# db_prod_size_entry = session.query(FeedProdStore) \
	# 	.filter_by(code=code, param_name=param_name) \
	# 	.first()

	try:
		order_id = get_child(order, "id")
		if order_id:
			order_id = int(order_id)
	except ValueError as e:
		order_id = 0

	try:
		order_type = get_child(order, "order_type")
		if order_type:
			order_type = int(order_type)
	except ValueError as e:
		order_type = 0

	try:
		creation_time = get_child(order, "timestamp")
		if creation_time:
			creation_time = int(creation_time)
	except ValueError as e:
		creation_time = 0

	db_order = LeadStore(site_name=site.name,
						id=order_id,
						order_type=order_type,
						time_create=creation_time,
						name=get_child(order, "name"),
						email=get_child(order, "email"),
						phone=get_child(order, "phone"),
						address=get_child(order, "address"),
						message=get_child(order, "message"),
						roistat=get_child(order, "roistat"),
						utm=get_child(order, "utm"),
						utm2=get_child(order, "utm2"),
						utm3=get_child(order, "utm3"),
						utm4=get_child(order, "utm4"),
						utm5=get_child(order, "utm5"),
						ip=get_child(order, "ip"))
	session.add(db_order)


def store_order_item(site, order, item):
	# db_prod_size_entry = session.query(FeedProdStore) \
	# 	.filter_by(code=, param_name=) \
	# 	.first()

	try:
		order_id = get_child(order, "id")
		if order_id:
			order_id = int(order_id)
	except ValueError as e:
		order_id = 0

	item_name = item.get("name")
	item_code = item.get("code")
	item_param = item.get("param")

	try:
		item_qty = item.get("qty")
		if item_qty:
			item_qty = int(item_qty)
	except ValueError as e:
		item_qty = 0

	try:
		item_price = item.get("price")
		if item_price:
			item_price = int(item_price)
	except ValueError as e:
		item_price = 0

	db_order_item = LeadOrderItems(site_name=site.name,
									id=order_id,
									name=item_name,
									code=item_code,
									param=item_param,
									qty=item_qty,
									price=item_price)

	session.add(db_order_item)

