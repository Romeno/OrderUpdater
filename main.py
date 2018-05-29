# -*- coding: utf-8 -*-

import logging
import os
import os.path
import time

import requests
from lxml import etree

import ou_db
from ou_common import get_child

program_name = "OrderUpdater"
crawl_delay = 0.15


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
		resp = requests.get("http://{}/orderxml_crm.php?start_id={}".format(site.name, from_id))
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

			last_id = ou_db.get_last_order_id(site)

			orders = get_new_orders(site, last_id)
			for i, order in enumerate(orders):
				if i % 100 == 0:
					logger.info("Storing {}'s new order".format(i))

				ou_db.store_order(site, order)

				order_items = order.find("order_items")
				if order_items:
					for item in order_items:
						ou_db.store_order_item(site, order, item)

			logger.info("Finished site {}".format(site.name))

	except Exception as e:
		logger.exception("Exception during {} run".format(program_name))
		raise

	logger.info("Finished!!!")


if __name__ == "__main__":
	main()