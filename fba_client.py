from __future__ import print_function

import time

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import sys


Messages = [
        '{"foo":"10"}',
        '{"bar":"30"}',
        '{"foo":"20"}',
        '{"bar":"20"}',
        '{"foo":"30"}',
        '{"bar":"10"}'
    ]

class fba_client(DatagramProtocol):
    def startProtocol(self):
        # Join the multicast address, so we can receive replies:
        self.transport.joinGroup("228.0.0.5")
        # Send to 228.0.0.5:9999 - all listeners on the multicast address
        # (including us) will receive this message.
        for i in Messages:
            self.transport.write(i.encode('utf-8'), ("228.0.0.5", int(sys.argv[1])))
            time.sleep(2)

    def datagramReceived(self, datagram, address):
        print("Data %s received from %s" % (datagram.decode(), repr(address)))


reactor.listenMulticast(3005, fba_client(), listenMultiple=True)
reactor.run()
