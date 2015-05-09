from wallace.models import *
from wallace.nodes import *
from wallace import db
from nose.tools import raises, assert_raises


class TestModels(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def add(self, *args):
        self.db.add_all(args)
        self.db.commit()

    ##################################################################
    # Node
    ##################################################################

    def test_create_node(self):
        """Create a basic node"""
        node = Node()
        self.add(node)

        assert len(node.uuid) == 32
        assert node.type == "base"
        assert node.creation_time
        assert len(node.infos()) == 0
        assert len(node.vectors(direction="outgoing")) == 0
        assert len(node.vectors(direction="incoming")) == 0
        assert len(node.vectors(direction="outgoing")) == 0
        assert len(node.vectors(direction="incoming")) == 0

    def test_different_node_uuids(self):
        """Test that two nodes have different uuids"""
        node1 = Node()
        node2 = Node()
        self.add(node1, node2)

        assert node1.uuid != node2.uuid

    def test_node_repr(self):
        """Test the repr of a node"""
        node = Node()
        self.add(node)

        assert repr(node).split("-") == ["Node", node.uuid[:6], "base"]

    def _check_single_connection(self, node1, node2):

        assert node1.is_connected(direction="to", other_node=node2)
        assert not node1.is_connected(direction="from", other_node=node2)
        assert node2.is_connected(direction="from", other_node=node1)
        assert not node2.is_connected(direction="to", other_node=node2)

        vector = node1.vectors(direction="outgoing")[0]
        assert vector.origin == node1
        assert vector.destination == node2

        assert node1.vectors(direction="outgoing") == [vector]
        assert len(node1.vectors(direction="incoming")) == 0
        assert len(node2.vectors(direction="outgoing")) == 0
        assert node2.vectors(direction="incoming") == [vector]

        assert len(node1.vectors(direction="incoming")) == 0
        assert len(node1.vectors(direction="outgoing")) == 1
        assert len(node2.vectors(direction="incoming")) == 1
        assert len(node2.vectors(direction="outgoing")) == 0

        assert node1.neighbors(connection="to") == [node2]
        assert len(node1.neighbors(connection="from")) == 0
        assert node2.neighbors(connection="from") == [node1]
        assert len(node2.neighbors(connection="to")) == 0

    def test_node_connect_to(self):
        """Test connecting one node to another"""
        node1 = Node()
        node2 = Node()
        node3 = Node()
        node4 = Node()
        self.add(node1, node2, node3, node4)
        self.db.commit()

        node1.connect_to(node2)

        assert node1.neighbors(connection="to") == [node2]

        assert node2.neighbors(connection="from") == [node1]

        node2.connect_to([node3, node4])

        assert node2.neighbors(connection="to") == [node3, node4]
        assert node3.neighbors(connection="from") == [node2]

        assert_raises(ValueError, node1.connect_to, other_node=node1)

        net = Network()
        self.add(net)

        failed = False
        try:
            node1.connect_to(net)
        except:
            failed = True
        assert failed is True

    def test_node_connect_from(self):
        """Test connecting one node from another"""
        node1 = Node()
        node2 = Node()

        self.add(node1)
        self.add(node2)
        self.db.commit()

        node1.connect_from(node2)
        self.add(node1, node2)

        self._check_single_connection(node2, node1)

    def test_node_outdegree(self):
        node1 = Node()
        self.db.add(node1)

        for i in xrange(5):
            assert len(node1.vectors(direction="outgoing")) == i
            new_node = Node()
            self.add(new_node)
            self.db.commit()
            node1.connect_to(new_node)
            self.add(new_node)

        assert len(node1.vectors(direction="outgoing")) == 5

        nodes = self.db.query(Node).all()

        node5 = [n for n in nodes if len(n.vectors(direction="outgoing")) == 5][0]
        assert node5 == node1

    def test_node_indegree(self):
        node1 = Node()
        self.db.add(node1)

        for i in xrange(5):
            assert len(node1.vectors(direction="incoming")) == i
            new_node = Node()
            node1.connect_from(new_node)
            self.add(new_node)

        assert len(node1.vectors(direction="incoming")) == 5

        nodes = self.db.query(Node).all()
        node5 = [n for n in nodes if len(n.vectors(direction="incoming")) == 5][0]
        assert node5 == node1

    def test_node_has_connection_to(self):
        node1 = Node()
        node2 = Node()
        self.add(node1, node2)
        self.db.commit()

        node1.connect_to(node2)
        self.add(node1, node2)

        assert node1.is_connected(direction="to", other_node=node2)
        assert not node2.is_connected(direction="to", other_node=node1)

    def test_node_has_connection_from(self):
        node1 = Node()
        node2 = Node()
        self.add(node1, node2)
        self.db.commit()

        node1.connect_to(node2)
        self.add(node1, node2)

        assert not node1.is_connected(direction="from", other_node=node2)
        assert node2.is_connected(direction="from", other_node=node1)

    ##################################################################
    # Vector
    ##################################################################

    def test_create_vector(self):
        """Test creating a vector between two nodes"""
        node1 = Node()
        node2 = Node()
        #vector = models.Vector(origin=node1, destination=node2)
        #self.add(node1, node2, vector)
        self.add(node1, node2)
        self.db.commit()

        node1.connect_to(node2)

        self._check_single_connection(node1, node2)
        #assert len(vector.transmissions) == 0

    def test_kill_vector(self):
        node1 = Node()
        node2 = Node()
        vector = Vector(origin=node1, destination=node2)
        self.add(node1, node2, vector)

        assert vector.status == "alive"

        vector.die()
        assert vector.status == "dead"

    def test_create_bidirectional_vectors(self):
        """Test creating a bidirectional connection between nodes"""
        node1 = Node()
        node2 = Node()
        vector1 = Vector(origin=node1, destination=node2)
        vector2 = Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert vector1.origin == node1
        assert vector1.destination == node2
        assert vector2.origin == node2
        assert vector2.destination == node1

        assert node1.vectors(direction="incoming") == [vector2]
        assert node1.vectors(direction="outgoing") == [vector1]
        assert node2.vectors(direction="incoming") == [vector1]
        assert node2.vectors(direction="outgoing") == [vector2]

        assert node1.is_connected(direction="to", other_node=node2)
        assert node1.is_connected(direction="from", other_node=node2)
        assert node2.is_connected(direction="to", other_node=node1)
        assert node2.is_connected(direction="from", other_node=node1)

        assert len(node1.vectors(direction="incoming")) == 1
        assert len(node2.vectors(direction="incoming")) == 1
        assert len(node1.vectors(direction="outgoing")) == 1
        assert len(node2.vectors(direction="outgoing")) == 1

        assert len(vector1.transmissions()) == 0
        assert len(vector2.transmissions()) == 0

    def test_vector_repr(self):
        """Test the repr of a vector"""
        node1 = Node()
        node2 = Node()
        vector1 = Vector(origin=node1, destination=node2)
        vector2 = Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert (repr(vector1).split("-") ==
                ["Vector", node1.uuid[:6], node2.uuid[:6]])
        assert (repr(vector2).split("-") ==
                ["Vector", node2.uuid[:6], node1.uuid[:6]])

    ##################################################################
    # Info
    ##################################################################

    def test_create_info(self):
        """Try creating an info"""
        node = Node()
        info = Info(origin=node, contents="foo")
        self.add(node, info)

        assert len(info.uuid) == 32
        assert info.type == "base"
        assert info.origin_uuid == node.uuid
        assert info.creation_time
        assert info.contents == "foo"
        assert len(info.transmissions()) == 0

        assert node.infos() == [info]

    def test_create_two_infos(self):
        """Try creating two infos"""
        node = Node()
        info1 = Info(origin=node, contents="bar")
        info2 = Info(origin=node, contents="foo")
        self.add(node, info1, info2)

        assert info1.uuid != info2.uuid
        assert info1.origin_uuid == info2.origin_uuid
        assert info1.creation_time != info2.creation_time
        assert info1.contents != info2.contents
        assert len(info1.transmissions()) == 0
        assert len(info2.transmissions()) == 0

        assert len(node.infos()) == 2
        assert info1 in node.infos()
        assert info2 in node.infos()

    def test_info_repr(self):
        """Check the info repr"""
        node = Node()
        info = Info(origin=node)
        self.add(info)

        assert repr(info).split("-") == ["Info", info.uuid[:6], "base"]

    @raises(ValueError)
    def test_info_write_twice(self):
        """Overwrite an info's contents."""
        node = Node()
        info = Info(origin=node, contents="foo")

        self.add(node, info)

        assert info.contents == "foo"
        info.contents = "ofo"

    ##################################################################
    # Transmission
    ##################################################################

    def test_create_transmission(self):
        """Try creating a transmission"""
        node1 = Node()
        node2 = Node()
        self.add(node1, node2)
        self.db.commit()
        node1.connect_to(node2)

        info = Info(origin=node1)
        node1.transmit(what=node1.infos()[0], to_whom=node2)
        #transmission = models.Transmission(info=info, destination=node2)
        #self.add(node1, node2, vector, info, transmission)

        transmission = node1.transmissions()[0]
        vector = node1.vectors()[0]

        assert len(transmission.uuid) == 32
        assert transmission.info_uuid == info.uuid
        assert transmission.origin_uuid == vector.origin_uuid
        assert transmission.destination_uuid == vector.destination_uuid
        assert transmission.transmit_time
        assert transmission.vector == vector
        assert vector.transmissions() == [transmission]

    def test_transmission_repr(self):
        node1 = Node()
        node2 = Node()
        self.add(node1, node2)

        node1.connect_to(node2)
        Info(origin=node1)

        node1.transmit(what=node1.infos()[0], to_whom=node2)
        transmission = node1.transmissions()[0]
        node1.vectors()[0]

        assert (repr(transmission).split("-") ==
                ["Transmission", transmission.uuid[:6]])

    def test_node_incoming_transmissions(self):
        agent1 = ReplicatorAgent()
        agent2 = ReplicatorAgent()
        agent3 = ReplicatorAgent()
        self.add(agent1, agent2, agent3)
        self.db.commit()

        agent1.connect_from(agent2)
        agent1.connect_from(agent3)
        self.add(agent1, agent2, agent3)

        info1 = Info(origin=agent2, contents="foo")
        info2 = Info(origin=agent3, contents="bar")
        self.add(info1, info2)

        agent2.transmit(what=info1, to_whom=agent1)
        agent3.transmit(what=info2, to_whom=agent1)
        self.db.commit()

        assert len(agent1.transmissions(direction="incoming")) == 2
        assert len(agent2.transmissions(direction="incoming")) == 0
        assert len(agent3.transmissions(direction="incoming")) == 0

    def test_node_outgoing_transmissions(self):
        agent1 = ReplicatorAgent()
        agent2 = ReplicatorAgent()
        agent3 = ReplicatorAgent()
        self.add(agent1, agent2, agent3)
        self.db.commit()

        agent1.connect_to(agent2)
        agent1.connect_to(agent3)
        self.add(agent1, agent2, agent3)

        info1 = Info(origin=agent1, contents="foo")
        info2 = Info(origin=agent1, contents="bar")
        self.add(info1, info2)

        agent1.transmit(what=info1, to_whom=agent2)
        agent1.transmit(what=info2, to_whom=agent3)
        self.db.commit()

        assert len(agent1.transmissions(direction="outgoing")) == 2
        assert len(agent2.transmissions(direction="outgoing")) == 0
        assert len(agent3.transmissions(direction="outgoing")) == 0
