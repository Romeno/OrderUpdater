#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import logging
from utils.process import SilentProcessPool

from ou_config import program_name

import ou_db
import ou_worker
import ou_common


def start_order_updater_instance(q):
    site = q
    try:
        ou = ou_worker.OrderUpdater(site)
        ou.run()
    except KeyboardInterrupt:
        raise
    except:
        pass

# end of StartCrawler


def main():
    from ou_config import db_username, db_password, db_host, db_name, process_pool_size, runner_log_name

    ou_common.init_logger(runner_log_name)

    logger = logging.getLogger(runner_log_name)

    try:
        ou_db.connect(db_username, db_password, db_host, db_name)

        sites = ou_db.get_sites()
        sites = [site.name for site in sites]

        ou_db.disconnect()

        pp = SilentProcessPool(poolLength=process_pool_size, worker=start_order_updater_instance,
                               data=sites)
        pp.logger_name = runner_log_name
        pp.Run()

        logger.info("Finished!!!")

    except Exception as e:
        logger.exception("Exception during {} run".format(program_name))
        raise

# end of main


if __name__ == "__main__":
    main()













