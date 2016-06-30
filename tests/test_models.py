"""Test the classes in models.py."""

from __future__ import print_function
import sys
from datetime import datetime
from wallace import models, db, nodes
from nose.tools import raises, assert_raises
from wallace.nodes import Agent, Source
from wallace.information import Gene
from wallace.transformations import Mutation


class TestModels(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def add(self, *args):
        self.db.add_all(args)
        self.db.commit()

    def test_models(self):

        def empty_tables(db):
            db.commit()
            self.setup()

        """####################
        ### Test Participant ##
        ####################"""

        print("")
        print("Testing models: Participant", end="\r")
        sys.stdout.flush()

        empty_tables(self.db)

        # create test participant
        ppt = models.Participant(worker_id="test",
                                 assignment_id="test",
                                 hit_id="test",
                                 mode="test")
        self.db.add(ppt)
        self.db.commit()
        ppt = models.Participant.query.one()

        net = models.Network()
        self.db.add(net)
        self.db.commit()
        net = models.Network.query.one()

        node1 = models.Node(network=net, participant=ppt)
        node2 = models.Node(network=net)

        info1 = models.Info(origin=node1)
        info2 = models.Info(origin=node1)
        info2.fail()
        q = models.Question(participant=ppt, text="blah", response="blah blah", number=1)

        # test attributes
        assert ppt.id == 1
        assert isinstance(ppt.creation_time, datetime)
        assert ppt.property1 is None
        assert ppt.property2 is None
        assert ppt.property3 is None
        assert ppt.property4 is None
        assert ppt.property5 is None
        assert ppt.failed is False
        assert ppt.time_of_death is None
        assert ppt.type == "participant"
        assert ppt.worker_id == "test"
        assert ppt.assignment_id == "test"
        assert ppt.hit_id == "test"
        assert ppt.mode == "test"
        assert ppt.unique_id == "test:test"
        assert ppt.end_time is None
        assert ppt.base_pay is None
        assert ppt.bonus is None
        assert ppt.status == "working"
        ppt.status = "submitted"
        self.db.commit()
        assert ppt.status == "submitted"

        # test json
        assert ppt.__json__() == {
            "id": 1,
            "type": "participant",
            "worker_id": "test",
            "assignment_id": "test",
            "unique_id": "test:test",
            "hit_id": "test",
            "mode": "test",
            "end_time": None,
            "base_pay": None,
            "bonus": None,
            "status": "submitted",
            "creation_time": ppt.creation_time,
            "failed": False,
            "time_of_death": None,
            "property1": None,
            "property2": None,
            "property3": None,
            "property4": None,
            "property5": None
        }

        # test nodes
        assert ppt.nodes() == [node1]
        assert ppt.nodes(type=Agent) == []
        assert ppt.nodes(failed=True) == []
        assert ppt.nodes(failed="all") == [node1]

        # test questions
        assert ppt.questions() == [q]
        assert ppt.questions(type=models.Question) == [q]

        # test infos
        assert ppt.infos() == [info1]
        assert ppt.infos(type=Gene) == []
        assert ppt.infos(failed=True) == [info2]
        assert len(ppt.infos(failed="all")) == 2

        # test fail
        ppt.fail()
        assert ppt.failed is True
        assert node1.failed is True
        assert node2.failed is False
        assert info1.failed is True
        assert info2.failed is True
        assert q.failed is True

        print("Testing models: Participant    passed!")
        sys.stdout.flush()

        """####################
        #### Test Question ####
        ####################"""

        print("Testing models: Question", end="\r")
        sys.stdout.flush()

        empty_tables(self.db)

        # create a question
        ppt = models.Participant(worker_id="test",
                                 assignment_id="test",
                                 hit_id="test",
                                 mode="test")
        self.db.add(ppt)
        self.db.commit()
        q = models.Question(
            participant=ppt,
            text="blah",
            response="blah blah",
            number=1)
        q = models.Question.query.one()

        # test attributes
        assert q.id == 1
        assert isinstance(q.creation_time, datetime)
        assert q.property1 is None
        assert q.property2 is None
        assert q.property3 is None
        assert q.property4 is None
        assert q.property5 is None
        assert q.failed is False
        assert q.time_of_death is None
        assert q.type == "question"
        assert q.participant == ppt
        assert q.participant_id == ppt.id
        assert q.number == 1
        assert q.text == "blah"
        assert q.response == "blah blah"

        # test fail
        q.fail()
        assert q.failed is True
        assert isinstance(q.time_of_death, datetime)

        print("Testing models: Question       passed!")
        sys.stdout.flush()

        """####################
        #### Test Network ####
        ####################"""

        print("Testing models: Network", end="\r")
        sys.stdout.flush()

        empty_tables(self.db)

        # create test network:
        net = models.Network()
        self.db.add(net)
        self.db.commit()
        net = models.Network.query.one()

        # create a participant
        participant = models.Participant(worker_id=str(1), hit_id=str(1), assignment_id=str(1), mode="test")
        self.db.add(participant)
        self.db.commit()

        # create some nodes
        node = models.Node(network=net)
        agent = Agent(network=net, participant=participant)
        source = Source(network=net)

        # create vectors
        source.connect(direction="to", whom=agent)
        agent.connect(direction="both", whom=node)

        # create some infos
        info = models.Info(origin=agent, contents="ethwth")
        gene = Gene(origin=source, contents="hkhkhkh")

        # conditionally transmit and transform
        source.transmit(what=models.Info)
        agent.receive()
        agent.transmit(what=Gene)
        models.Transformation(info_in=gene, info_out=info)

        # Test attributes
        assert net.id == 1
        assert isinstance(net.creation_time, datetime)
        assert net.property1 is None
        assert net.property2 is None
        assert net.property3 is None
        assert net.property4 is None
        assert net.property5 is None
        assert net.failed is False
        assert net.time_of_death is None
        assert net.type == "network"
        assert isinstance(net.max_size, int)
        assert net.max_size == 1e6
        assert isinstance(net.full, bool)
        assert net.full is False
        assert isinstance(net.role, unicode)
        assert net.role == "default"

        # test __repr__()
        assert repr(net) == "<Network-1-network with 3 nodes, 3 vectors, 2 infos, 1 transmissions and 1 transformations>"

        # test __json__()
        assert net.__json__() == {
            "id": 1,
            "type": "network",
            "max_size": 1e6,
            "full": False,
            "role": "default",
            "creation_time": net.creation_time,
            "failed": False,
            "time_of_death": None,
            "property1": None,
            "property2": None,
            "property3": None,
            "property4": None,
            "property5": None
        }

        # test nodes()
        for n in [node, agent, source]:
            assert n in net.nodes()

        assert net.nodes(type=Agent) == [agent]

        assert net.nodes(failed=True) == []
        for n in [node, agent, source]:
            assert n in net.nodes(failed="all")

        assert net.nodes(participant_id=1) == [agent]

        # test size()
        assert net.size() == 3
        assert net.size(type=Source) == 1
        assert net.size(type=Agent) == 1
        assert net.size(failed=True) == 0
        assert net.size(failed="all") == 3

        # test infos()
        assert len(net.infos(failed="all")) == 2
        assert len(net.infos(type=models.Info, failed="all")) == 2
        assert len(net.infos(type=Gene, failed="all")) == 1
        assert len(net.infos(type=Gene)) == 1
        assert len(net.infos(failed=True)) == 0

        # test Network.transmissions()
        assert len(net.transmissions(failed="all")) == 1
        assert len(net.transmissions(failed=True)) == 0
        assert len(net.transmissions(failed=False)) == 1
        assert len(net.transmissions(status="pending", failed="all")) == 0
        assert len(net.transmissions(status="received", failed="all")) == 1

        # test Network.transformations()
        assert len(net.transformations(failed="all")) == 1
        assert len(net.transformations(failed="all", type=Mutation)) == 0
        assert len(net.transformations(failed="all", type=models.Transformation)) == 1

        for t in net.transformations(failed="all"):
            assert type(t.node) == Agent

        # test latest_transmission_recipient
        assert net.latest_transmission_recipient() == agent

        # test Network.vectors()
        assert len(net.vectors(failed="all")) == 3
        assert len(net.vectors(failed=False)) == 3
        assert len(net.vectors(failed=True)) == 0

        # test fail()
        net.fail()
        assert net.nodes() == []
        assert len(net.nodes(failed=True)) == 3
        assert len(net.nodes(failed="all")) == 3
        assert net.infos() == []
        assert net.transmissions() == []
        assert net.vectors() == []
        assert net.transformations() == []

        print("Testing models: Network        passed!")
        sys.stdout.flush()

        """####################
        ###### Test Node ######
        ####################"""

        print("Testing models: Node", end="\r")
        sys.stdout.flush()

        empty_tables(self.db)

        # create nodes
        net = models.Network()
        self.db.add(net)
        self.db.commit()
        net = models.Network.query.one()

        ppt = models.Participant(worker_id="test",
                                 assignment_id="test",
                                 hit_id="test",
                                 mode="test")
        self.db.add(ppt)
        self.db.commit()
        ppt = models.Participant.query.one()

        node1 = models.Node(network=net)
        node2 = models.Node(network=net, participant=ppt)
        v = node1.connect(node2)[0]
        info1 = models.Info(origin=node1)
        info2 = models.Info(origin=node2)
        info2.fail()
        t = node1.transmit()

        # Test attributes
        assert node1.id == 1
        assert isinstance(node1.creation_time, datetime)
        assert node1.property1 is None
        assert node1.property2 is None
        assert node1.property3 is None
        assert node1.property4 is None
        assert node1.property5 is None
        assert node1.failed is False
        assert node1.time_of_death is None
        assert node1.type == "node"
        assert node1.network == net
        assert node1.network_id == 1
        assert node1.participant is None
        assert node1.participant_id is None
        assert node2.participant == ppt
        assert node2.participant_id == 1

        # test __repr__
        assert repr(node1) == "Node-1-node"

        # test __json__
        assert node1.__json__() == {
            "id": 1,
            "type": "node",
            "network_id": 1,
            "creation_time": node1.creation_time,
            "time_of_death": None,
            "failed": False,
            "participant_id": None,
            "property1": None,
            "property2": None,
            "property3": None,
            "property4": None,
            "property5": None
        }

        # test vectors
        assert node1.vectors() == [v]
        assert node1.vectors(direction="outgoing") == [v]
        assert node1.vectors(direction="incoming") == []
        assert node1.vectors(failed=True) == []
        assert node2.vectors() == [v]
        assert node2.vectors(direction="incoming") == [v]
        assert node2.vectors(direction="outgoing") == []
        assert node2.vectors(failed=True) == []

        # test neighbors
        assert node1.neighbors() == [node2]
        assert node1.neighbors(type=Agent) == []
        assert node1.neighbors(direction="from") == []
        assert node1.neighbors(direction="either") == [node2]
        assert node1.neighbors(direction="both") == []
        assert node2.neighbors() == []
        assert node2.neighbors(type=Agent) == []
        assert node2.neighbors(direction="from") == [node1]
        assert node2.neighbors(direction="either") == [node1]
        assert node2.neighbors(direction="both") == []

        # test is_connected
        assert node1.is_connected(node2)
        assert not node2.is_connected(node1)
        assert not node1.is_connected(node2, direction="from")
        assert node2.is_connected(node1, direction="from")
        assert node1.is_connected(node2, direction="either")
        assert node2.is_connected(node1, direction="either")
        assert not node1.is_connected(node2, direction="both")
        assert not node2.is_connected(node1, direction="both")

        assert node1.is_connected([node2, node2]) == [True, True]

        # test infos
        assert node1.infos() == [info1]
        assert node2.infos() == []
        assert node1.infos(type=Gene) == []
        assert node2.infos(type=Gene) == []
        assert node1.infos(failed=True) == []
        assert node2.infos(failed=True) == [info2]
        assert node1.infos(failed="all") == [info1]
        assert node2.infos(failed="all") == [info2]

        # test received infos
        node2.receive()
        assert node1.received_infos() == []
        assert node2.received_infos() == [info1]
        assert node2.received_infos(type=Gene) == []

        # test transmissions
        assert node1.transmissions() == [t]
        assert node1.transmissions(direction="incoming") == []
        assert node1.transmissions(direction="all") == [t]
        assert node1.transmissions(status="pending") == []
        assert node1.transmissions(status="received") == [t]
        assert node2.transmissions() == []
        assert node2.transmissions(direction="incoming") == [t]
        assert node2.transmissions(direction="all") == [t]
        assert node2.transmissions(direction="incoming",
                                   status="pending") == []
        assert node2.transmissions(direction="incoming",
                                   status="received") == [t]

        # test transformations
        info2.failed = False
        tf = models.Transformation(info_in=info1, info_out=info2)
        assert node1.transformations() == []
        assert node2.transformations() == [tf]
        assert node2.transformations(type=Mutation) == []

        # test fail
        node2.fail()
        assert node2.failed is True
        assert info2.failed is True
        assert t.failed is True
        assert v.failed is True
        assert tf.failed is True
        assert node1.failed is False

        # test connect
        assert len(models.Vector.query.filter_by(
            origin_id=1,
            destination_id=2).all()) == 1
        assert len(models.Vector.query.filter_by(
            origin_id=2,
            destination_id=1).all()) == 0
        assert len(models.Vector.query.all()) == 1

        # test transmit
        assert len(models.Transmission.query.all()) == 1
        assert len(models.Transmission.query.filter_by(
            origin_id=1).all()) == 1
        assert len(models.Transmission.query.filter_by(
            origin_id=2).all()) == 0
        assert len(models.Transmission.query.filter_by(
            info_id=1).all()) == 1

        print("Testing models: Node           passed!")
        sys.stdout.flush()

        """####################
        ##### Test Vector #####
        ####################"""

        print("Testing models: Vector", end="\r")
        sys.stdout.flush()

        empty_tables(self.db)

        # create vector
        net = models.Network()
        self.db.add(net)
        self.db.commit()
        net = models.Network.query.one()

        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        v = node1.connect(node2)[0]
        v2 = node2.connect(node1)[0]
        info1 = models.Info(origin=node1)
        t = node1.transmit()

        # Test attributes
        assert v.id == 1
        assert isinstance(v.creation_time, datetime)
        assert v.property1 is None
        assert v.property2 is None
        assert v.property3 is None
        assert v.property4 is None
        assert v.property5 is None
        assert v.failed is False
        assert v.time_of_death is None
        assert v.type == "vector"
        assert v.network == net
        assert v.network_id == 1
        assert v.origin_id == 1
        assert v.origin == node1
        assert v.destination_id == 2
        assert v.destination == node2
        assert v.network_id == 1
        assert v.network == net

        # test repr
        assert repr(v) == "Vector-1-vector"

        # test __json__
        assert v.__json__() == {
            "id": 1,
            "origin_id": 1,
            "destination_id": 2,
            "network_id": 1,
            "creation_time": v.creation_time,
            "failed": False,
            "time_of_death": None,
            "property1": None,
            "property2": None,
            "property3": None,
            "property4": None,
            "property5": None
        }

        # test transmissions
        assert v.transmissions() == [t]
        assert v2.transmissions() == []
        assert v.transmissions(status="received") == []

        # test fail
        v.fail()
        assert v.failed is True
        assert v2.failed is False
        assert info1.failed is False
        assert t.failed is True

        print("Testing models: Vector         passed!")
        sys.stdout.flush()



    ##################################################################
    # Node
    ##################################################################

    def test_create_node(self):
        """Create a basic node"""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        self.add(node)

        assert isinstance(node.id, int)
        assert node.type == "node"
        assert node.creation_time
        assert len(node.infos()) == 0
        assert len(node.vectors(direction="outgoing")) == 0
        assert len(node.vectors(direction="incoming")) == 0
        assert len(node.vectors(direction="outgoing")) == 0
        assert len(node.vectors(direction="incoming")) == 0

    def test_different_node_ids(self):
        """Test that two nodes have different ids"""
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        self.add(node1, node2)

        assert node1.id != node2.id

    def test_node_repr(self):
        """Test the repr of a node"""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        self.add(node)

        assert repr(node).split("-") == ["Node", str(node.id), "node"]

    def _check_single_connection(self, node1, node2):

        assert node1.is_connected(direction="to", whom=node2)
        assert not node1.is_connected(direction="from", whom=node2)
        assert node2.is_connected(direction="from", whom=node1)
        assert not node2.is_connected(direction="to", whom=node2)

        vector = node1.vectors(direction="outgoing")[0]
        assert vector.origin_id == node1.id
        assert vector.destination_id == node2.id

        assert node1.vectors(direction="outgoing") == [vector]
        assert len(node1.vectors(direction="incoming")) == 0
        assert len(node2.vectors(direction="outgoing")) == 0
        assert node2.vectors(direction="incoming") == [vector]

        assert len(node1.vectors(direction="incoming")) == 0
        assert len(node1.vectors(direction="outgoing")) == 1
        assert len(node2.vectors(direction="incoming")) == 1
        assert len(node2.vectors(direction="outgoing")) == 0

        assert node1.neighbors(direction="to") == [node2]
        assert len(node1.neighbors(direction="from")) == 0
        assert node2.neighbors(direction="from") == [node1]
        assert len(node2.neighbors(direction="to")) == 0

    def test_node_connect(self):
        """Test connecting one node to another"""
        net = models.Network()
        self.db.add(net)
        self.db.commit()

        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        node3 = models.Node(network=net)
        node4 = models.Node(network=net)
        # self.add(node1, node2, node3, node4)
        # self.db.commit()

        node1.connect(whom=node2)

        assert node1.neighbors(direction="to") == [node2]

        assert node2.neighbors(direction="from") == [node1]

        node2.connect(whom=[node3, node4])

        for n in node2.neighbors(direction="to"):
            assert n in [node3, node4]
        assert node3.neighbors(direction="from") == [node2]

        assert_raises(ValueError, node1.connect, whom=node1)

        net = models.Network()
        self.add(net)

        assert_raises(TypeError, node1.connect, whom=net)

    def test_node_outdegree(self):
        net = models.Network()
        self.add(net)
        node1 = models.Node(network=net)
        self.db.add(node1)

        for i in xrange(5):
            assert len(node1.vectors(direction="outgoing")) == i
            new_node = models.Node(network=net)
            self.add(new_node)
            self.db.commit()
            node1.connect(whom=new_node)
            self.add(new_node)

        assert len(node1.vectors(direction="outgoing")) == 5

        nodes = self.db.query(models.Node).all()

        node5 = [n for n in nodes if len(n.vectors(direction="outgoing")) == 5][0]
        assert node5 == node1

    def test_node_indegree(self):
        net = models.Network()
        self.add(net)
        node1 = models.Node(network=net)
        self.db.add(node1)
        self.db.commit()

        for i in xrange(5):
            assert len(node1.vectors(direction="incoming")) == i
            new_node = models.Node(network=net)
            self.db.add(new_node)
            self.db.commit()
            node1.connect(direction="from", whom=new_node)
            self.add(new_node)

        assert len(node1.vectors(direction="incoming")) == 5

        nodes = self.db.query(models.Node).all()
        node5 = [n for n in nodes if len(n.vectors(direction="incoming")) == 5][0]
        assert node5 == node1

    def test_node_has_connection_to(self):
        net = models.Network()
        self.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        self.add(node1, node2)
        self.db.commit()

        node1.connect(whom=node2)
        self.add(node1, node2)

        assert node1.is_connected(direction="to", whom=node2)
        assert not node2.is_connected(direction="to", whom=node1)

    def test_node_has_connection_from(self):
        net = models.Network()
        self.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        self.add(node1, node2)
        self.db.commit()

        node1.connect(whom=node2)
        self.add(node1, node2)

        assert not node1.is_connected(direction="from", whom=node2)
        assert node2.is_connected(direction="from", whom=node1)

    ##################################################################
    # Vector
    ##################################################################

    def test_create_vector(self):
        """Test creating a vector between two nodes"""
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        #vector = models.Vector(origin=node1, destination=node2)
        #self.add(node1, node2, vector)
        self.add(node1, node2)
        self.db.commit()

        node1.connect(whom=node2)

        self._check_single_connection(node1, node2)
        #assert len(vector.transmissions) == 0

    def test_kill_vector(self):
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        vector = models.Vector(origin=node1, destination=node2)
        self.add(node1, node2, vector)

        assert vector.failed is False

        vector.fail()
        assert vector.failed is True

    def test_create_bidirectional_vectors(self):
        """Test creating a bidirectional connection between nodes"""
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        vector1 = models.Vector(origin=node1, destination=node2)
        vector2 = models.Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert vector1.origin_id == node1.id
        assert vector1.destination_id == node2.id
        assert vector2.origin_id == node2.id
        assert vector2.destination_id == node1.id

        assert node1.vectors(direction="incoming") == [vector2]
        assert node1.vectors(direction="outgoing") == [vector1]
        assert node2.vectors(direction="incoming") == [vector1]
        assert node2.vectors(direction="outgoing") == [vector2]

        assert node1.is_connected(direction="to", whom=node2)
        assert node1.is_connected(direction="from", whom=node2)
        assert node2.is_connected(direction="to", whom=node1)
        assert node2.is_connected(direction="from", whom=node1)

        assert len(node1.vectors(direction="incoming")) == 1
        assert len(node2.vectors(direction="incoming")) == 1
        assert len(node1.vectors(direction="outgoing")) == 1
        assert len(node2.vectors(direction="outgoing")) == 1

        assert len(vector1.transmissions()) == 0
        assert len(vector2.transmissions()) == 0

    def test_vector_repr(self):
        """Test the repr of a vector"""
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        vector1 = models.Vector(origin=node1, destination=node2)
        vector2 = models.Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert (repr(vector1).split("-") ==
                ["Vector", str(node1.id), str(node2.id)])
        assert (repr(vector2).split("-") ==
                ["Vector", str(node2.id), str(node1.id)])

    ##################################################################
    # Info
    ##################################################################

    def test_create_info(self):
        """Try creating an info"""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        info = models.Info(origin=node, contents="foo")
        self.add(node, info)

        assert isinstance(info.id, int)
        assert info.type == "info"
        assert info.origin_id == node.id
        assert info.creation_time
        assert info.contents == "foo"
        assert len(info.transmissions()) == 0

        assert node.infos() == [info]

    def test_create_two_infos(self):
        """Try creating two infos"""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        info1 = models.Info(origin=node, contents="bar")
        info2 = models.Info(origin=node, contents="foo")
        self.add(node, info1, info2)

        assert info1.id != info2.id
        assert info1.origin_id == info2.origin_id
        assert info1.creation_time != info2.creation_time
        assert info1.contents != info2.contents
        assert len(info1.transmissions()) == 0
        assert len(info2.transmissions()) == 0

        assert len(node.infos()) == 2
        assert info1 in node.infos()
        assert info2 in node.infos()

    def test_info_repr(self):
        """Check the info repr"""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        info = models.Info(origin=node)
        self.add(info)

        assert repr(info).split("-") == ["Info", str(info.id), "info"]

    @raises(ValueError)
    def test_info_write_twice(self):
        """Overwrite an info's contents."""
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        info = models.Info(origin=node, contents="foo")

        self.add(node, info)

        assert info.contents == "foo"
        info.contents = "ofo"

    ##################################################################
    # Transmission
    ##################################################################

    def test_create_transmission(self):
        """Try creating a transmission"""
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        self.add(node1, node2)
        self.db.commit()
        node1.connect(whom=node2)

        info = models.Info(origin=node1)
        node1.transmit(what=node1.infos()[0], to_whom=node2)
        #transmission = models.Transmission(info=info, destination=node2)
        #self.add(node1, node2, vector, info, transmission)

        transmission = node1.transmissions()[0]
        vector = node1.vectors()[0]

        assert isinstance(transmission.id, int)
        assert transmission.info_id == info.id
        assert transmission.origin_id == vector.origin_id
        assert transmission.destination_id == vector.destination_id
        assert transmission.creation_time
        assert transmission.vector == vector
        assert vector.transmissions() == [transmission]

    def test_transmission_repr(self):
        net = models.Network()
        self.db.add(net)
        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        self.add(node1, node2)

        node1.connect(whom=node2)
        models.Info(origin=node1)

        node1.transmit(what=node1.infos()[0], to_whom=node2)
        transmission = node1.transmissions()[0]
        node1.vectors()[0]

        assert (repr(transmission).split("-") ==
                ["Transmission", str(transmission.id)])

    def test_node_incoming_transmissions(self):
        net = models.Network()
        self.db.add(net)
        agent1 = nodes.ReplicatorAgent(network=net)
        agent2 = nodes.ReplicatorAgent(network=net)
        agent3 = nodes.ReplicatorAgent(network=net)
        self.add(agent1, agent2, agent3)
        self.db.commit()

        agent1.connect(direction="from", whom=[agent2, agent3])
        self.add(agent1, agent2, agent3)

        info1 = models.Info(origin=agent2, contents="foo")
        info2 = models.Info(origin=agent3, contents="bar")
        self.add(info1, info2)

        agent2.transmit(what=info1, to_whom=agent1)
        agent3.transmit(what=info2, to_whom=agent1)
        self.db.commit()

        assert len(agent1.transmissions(direction="incoming")) == 2
        assert len(agent2.transmissions(direction="incoming")) == 0
        assert len(agent3.transmissions(direction="incoming")) == 0

    def test_node_outgoing_transmissions(self):
        net = models.Network()
        self.db.add(net)
        agent1 = nodes.ReplicatorAgent(network=net)
        agent2 = nodes.ReplicatorAgent(network=net)
        agent3 = nodes.ReplicatorAgent(network=net)
        self.add(agent1, agent2, agent3)
        self.db.commit()

        agent1.connect(whom=agent2)
        agent1.connect(whom=agent3)
        self.add(agent1, agent2, agent3)

        info1 = models.Info(origin=agent1, contents="foo")
        info2 = models.Info(origin=agent1, contents="bar")
        self.add(info1, info2)

        agent1.transmit(what=info1, to_whom=agent2)
        agent1.transmit(what=info2, to_whom=agent3)
        self.db.commit()

        assert len(agent1.transmissions(direction="outgoing")) == 2
        assert len(agent2.transmissions(direction="outgoing")) == 0
        assert len(agent3.transmissions(direction="outgoing")) == 0

    def test_property_node(self):
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        node.property1 = "foo"
        self.add(node)

        assert node.property1 == "foo"

    def test_creation_time(self):
        net = models.Network()
        self.db.add(net)
        node = models.Node(network=net)
        self.add(node)
        assert node.creation_time is not None
