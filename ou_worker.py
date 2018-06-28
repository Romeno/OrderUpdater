#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import time

import requests
from lxml import etree

from sqlalchemy.exc import SQLAlchemyError

import ou_db
from ou_common import get_child, to_int, init_logger
from ou_config import program_name, crawl_delay, start_time, base_worker_logger_name


class OrderUpdater:
	def __init__(self, site_name):
		self.site_name = site_name
		self.worker_logger_name = "{}{}.log".format(base_worker_logger_name, self.site_name)

	def run(self):
		from ou_config import db_username, db_password, db_host, db_name

		init_logger(self.worker_logger_name)

		logger = logging.getLogger(self.worker_logger_name)

		logger.info("Started site {}".format(self.site_name))

		try:
			ou_db.connect(db_username, db_password, db_host, db_name)

			try:
				last_id = ou_db.get_last_order_id(self.site_name)

				orders_orig = self.get_new_orders(self.site_name, last_id + 1)
				if orders_orig is None:
					logger.error("Skipping site {} due to error when getting order list".format(self.site_name))
					return

				orders = sorted(orders_orig, key=lambda e: to_int(get_child(e, "id")))

				for i, order in enumerate(orders):
					if i % 100 == 0:
						logger.info("Storing {}'s new order".format(i))
						try:
							ou_db.session.commit()
						except SQLAlchemyError as e:
							logger.error("Potential error rolling back transaction")
							ou_db.session.rollback()

					ou_db.store_order(self.site_name, order)

					order_items = order.find("order_items")
					if order_items:
						for item in order_items:
							ou_db.store_order_item(self.site_name, order, item)

				ou_db.session.commit()
				logger.info("Finished site {}".format(self.site_name))
			except Exception as e:
				logger.exception("Exception during {} run".format(program_name))
				logger.error("Skipping site {}".format(self.site_name))

		except Exception as e:
			logger.exception("Exception during {} run".format(program_name))
			raise
		finally:
			ou_db.disconnect()

		logger.info("Finished!!!")

	def get_new_orders(self, site_name, from_id):
		logger = logging.getLogger(self.worker_logger_name)

		logger.info("Getting orders from id {}".format(from_id))

		try:
			url = "http://{}/orderxml_crm.php?start_id={}&start_time={}".format(site_name, from_id, start_time)
			resp = requests.get(url, verify=False)
			if resp.ok:
				root = etree.fromstring(resp.content)
				if len(root) == 0:
					logger.info("Empty xml for site {}".format(site_name))
					return None

				return root[0]
			else:
				logger.error("Error {} when getting {} orders".format(resp.status_code, site_name))
				return None
		except requests.RequestException as e:
			logger.exception("Requests exception when getting {} orders".format(site_name))
			return None

