#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import socket
from Asterisk.Config import Config
from Asterisk.Manager import CoreManager
import Asterisk.Manager
import Asterisk.Util
import logging
import requests
import sys
from web_server_conf import ws

reload(sys)
sys.setdefaultencoding('utf-8')


class MyManager(CoreManager):
    def on_Event(self, event):
        # Asterisk.Util.dump_packet(event)
        if event['Event'] == 'Newchannel' and event['CallerIDNum'] != '<unknown>' and len(event['CallerIDNum']) > 3:
            logging.info('  Caller ID: ' + repr(event['CallerIDNum']).decode("unicode_escape"))
            r = requests.get(ws["ws_address"] + event['CallerIDNum'])
            try:
                rj = r.json()
            except ValueError, r:
                logging.ERROR(r)

            # logging.info('  1C data' + repr(rj).decode("unicode_escape"))
            if 'WorkName' in rj and rj['WorkName'] is not None:
                clientname = rj['WorkName']
                logging.info('      Client: ' + repr(clientname).decode("unicode_escape"))
                result_setvar = MyManager.Setvar(self, event['Channel'], 'CALLERID(Name)', clientname)
                logging.info('      result setvar CALLERID(Name): ' + str(result_setvar))
                logging.info('      Manager: ' + repr(rj['Manager']).decode("unicode_escape"))
                if rj['ManagerPhone'] != '' and rj['ManagerPhone'] is not None:
                    logging.info('      Manager phone: ' + repr(rj['ManagerPhone']).decode("unicode_escape"))
                    logging.info('      Manager Online: ' + str(rj['ManagerOnLine']))
                    if rj['ManagerOnLine']:
                        result_redirect = MyManager.Redirect(self, event['Channel'], 'default', rj['ManagerPhone'],
                                                             event['Priority'])
                        logging.info('      result redirect: ' + str(result_redirect))


def main2():
    manager = MyManager(*Config().get_connection())

    try:
        print '#', repr(manager)
        print
        manager.serve_forever()

    except KeyboardInterrupt, e:
        raise SystemExit


def main(argv):
    max_reconnects = 100
    reconnect_delay = 2

    logging.basicConfig(filename=u'asterisk_test_log.log', level=logging.INFO, format=u'%(levelname)-8s [%(asctime)s] %(message)s')
    logging.info('start service.')

    while True:
        try:
            main2()

        except Asterisk.Manager.GoneAwayError, e:
            print '#', str(e)

        except socket.error, e:
            print
            print '# Connect error:', e[1]
            reconnect_delay *= 2

        print '# Waiting', reconnect_delay, 'seconds before reconnect.'
        print '# Will try', max_reconnects, 'more times before exit..'

        max_reconnects -= 1
        time.sleep(reconnect_delay)
        print '# Reconnecting...'


if __name__ == '__main__':
    main(sys.argv[1:])
