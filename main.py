# -*- coding: utf-8 -*-

import logging
import os
import os.path
import time

import requests
from lxml import etree

import ou_db
from ou_common import get_child, to_int

program_name = "OrderUpdater"
crawl_delay = 0.15
start_time = 1527125400			# 24 May 01:30


def init_logger():
	from logging.config import dictConfig

	logging_config = {
		'version': 1,
		'disable_existing_loggers': False,
		'formatters': {
			'f': {
				'format':
					'%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
			}
		},
		'handlers': {
			'h': {
				'class': 'logging.handlers.RotatingFileHandler',
				'formatter': 'f',
				'level': 'DEBUG',
				'filename': 'errors.log',
				'maxBytes': 10485760,
				'backupCount': 20,
				'encoding': 'utf8'
			}
		},
		'root': {
			'handlers': ['h'],
			'level': logging.INFO,
		},
	}

	dictConfig(logging_config)


def get_new_orders(site, from_id):
	logger = logging.getLogger()

	logger.info("Getting orders from id {}".format(from_id))

	try:
		url = "http://{}/orderxml_crm.php?start_id={}&start_time={}".format(site.name, from_id, start_time)
		resp = requests.get(url, verify=False)
		if resp.ok:
			root = etree.fromstring(resp.content)
			if len(root) == 0:
				logger.warning("Empty xml of orders for some reason for site {}".format(site.name))
				return None

			return root[0]
		else:
			logger.error("Error {} when getting {} orders".format(resp.status_code, site.name))
			return None
	except requests.RequestException as e:
		logger.exception("Requests exception when getting {} orders".format(site.name))
		return None


def main():
	init_logger()

	db_username = "postgres"
	db_password = ""
	db_host = "localhost"
	db_name = "Crm"

	logger = logging.getLogger()

	try:
		ou_db.connect(db_username, db_password, db_host, db_name)

		for site in ou_db.get_sites():
			logger.info("Started site {}".format(site.name))

			try:
				last_id = ou_db.get_last_order_id(site)

				orders_orig = get_new_orders(site, last_id + 1)
				if orders_orig is None:
					logger.error("Skipping site {} due to error when getting order list".format(site.name))
					continue

				orders = sorted(orders_orig, key=lambda e: to_int(get_child(e, "id")))

				for i, order in enumerate(orders):
					if i % 100 == 0:
						logger.info("Storing {}'s new order".format(i))
						ou_db.session.commit()

					ou_db.store_order(site, order)

					order_items = order.find("order_items")
					if order_items:
						for item in order_items:
							ou_db.store_order_item(site, order, item)

				ou_db.session.commit()
				logger.info("Finished site {}".format(site.name))
			except Exception as e:
				logger.exception("Exception during {} run".format(program_name))
				logger.error("Skipping site {}".format(site.name))

	except Exception as e:
		logger.exception("Exception during {} run".format(program_name))
		raise

	logger.info("Finished!!!")


if __name__ == "__main__":
	main()