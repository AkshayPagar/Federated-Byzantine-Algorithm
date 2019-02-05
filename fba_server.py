from __future__ import print_function
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import sys
import pickledb
import json

ports={3000,3001,3002,3003}

class fba_server(DatagramProtocol):

    def __init__(self):
        self.States = ['none','init', 'vote', 'accept', 'confirm']
        self.current_state='none'
        self.Ballot={'Value':'','Counter':0}
        print("\nServer with port number", sys.argv[1], "is up and running!")
        self.changeState('init')
        self.Primary=False
        self.clientAddress=''
        self.Approved=False

    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("228.0.0.5")


    def datagramReceived(self, datagram, address):
        print("\nDatagram %s received from %s" % (repr(datagram), repr(address)))
        self.Ballot['Value']=datagram.decode()
        self.Ballot['Counter']=self.Ballot['Counter']+1

     # Rather than replying to the group multicast address, we send the
            # reply directly (unicast) to the originating port:

        if address[1] == 3005 and self.current_state == 'init':
            self.Approved = False
            self.Primary=True
            self.clientAddress=address
            for i in ports:
                if str(i) != sys.argv[1]:
                    self.transport.write(datagram, (address[0],int(i)))
            self.changeState("vote")

        elif self.current_state == 'init':
            self.Approved=False
            for i in ports:
                self.transport.write(datagram, (address[0],int(i)))
            self.changeState("vote")
            time.sleep(0.5)
        if self.current_state == 'vote':
            if(self.Ballot['Counter'] >= 4):
                if not self.Approved:
                    print("\nBallot State:"+str(self.Ballot)+ "=> Voting Done! Changing state to Accept!")
                    self.changeState('accept')
                    self.accept_handler(datagram)
                    self.Approved=True
                else:
                    print("\nBallot State:" + str(self.Ballot) + "=> Voting Done! Changing state to Accept!")

            else:
                print("\nBallot State:"+str(self.Ballot)+ "=>Nodes are voting ")

    def changeState(self, state):
        prev_state=self.current_state
        self.current_state=state;
        print("\nBallot state changing from '"+prev_state+"' to '"+self.current_state+"'")

    def confirmUpdate(self,datagram):
        print("\nData is ready to be written to database...")
        db_name = 'assignment3_' + sys.argv[1] + '.db'
        db = pickledb.load(db_name, False)
        json_data = datagram.decode('utf-8')
        data = json.loads(json_data)
        for key in data:
            if db.get(key):
                db.set(key, int(db.get(key)) + int(data[key]))
            else:
                db.set(key, data[key])
        db.dump()
        print(self.Ballot['Value']," is committed to database ",db_name ,"!\n")
        print("Database Status:\n********************")
        for i in db.getall():
            data = db.dgetall(i)
            print(i, data)
        print("\n********************")
        if self.Primary:
            data=b'Data'+datagram+b'is accepted and written to database!'
            self.transport.write(data, (self.clientAddress))
        time.sleep(1)



    def accept_handler(self,datagram):
        if self.current_state=='accept':
            if self.Ballot['Counter']>=3:
                print(self.Ballot)
                print("\nThreshold of 3/4 has been reached! Changing state to confirm!")
                self.changeState('confirm')
                self.confirmUpdate(datagram)
                self.resetState()

    def resetState(self):
        print("\nResetting Ballot to 'init' state!")
        self.changeState('init')
        self.Ballot = {'Value': '', 'Counter': 0}



# We use listenMultiple=True so that we can run MulticastServer.py and
# MulticastClient.py on same machine:
port = sys.argv[1]
reactor.listenMulticast(int(port), fba_server(),
                        listenMultiple=True)
reactor.run()
