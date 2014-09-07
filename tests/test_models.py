from wallace import models, db
from nose.tools import raises
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import FlushError
import time


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
    ## Node
    ##################################################################

    def test_create_node(self):
        """Create a basic node"""
        node = models.Node()
        self.add(node)

        assert len(node.uuid) == 32
        assert node.type == "base"
        assert node.creation_time
        assert len(node.information) == 0
        assert node.outdegree == 0
        assert node.indegree == 0
        assert len(node.outgoing_vectors) == 0
        assert len(node.incoming_vectors) == 0

    def test_different_node_uuids(self):
        """Test that two nodes have different uuids"""
        node1 = models.Node()
        node2 = models.Node()
        self.add(node1, node2)

        assert node1.uuid != node2.uuid

    def test_node_repr(self):
        """Test the repr of a node"""
        node = models.Node()
        self.add(node)

        assert repr(node).split("-") == ["Node", node.uuid[:6], "base"]

    def _check_single_connection(self, node1, node2):
        assert node1.has_connection_to(node2)
        assert not node1.has_connection_from(node2)
        assert node2.has_connection_from(node1)
        assert not node2.has_connection_to(node1)

        vector = node1.outgoing_vectors[0]
        assert vector.origin_uuid == node1.uuid
        assert vector.destination_uuid == node2.uuid

        assert node1.outgoing_vectors == [vector]
        assert len(node1.incoming_vectors) == 0
        assert len(node2.outgoing_vectors) == 0
        assert node2.incoming_vectors == [vector]

        assert node1.indegree == 0
        assert node1.outdegree == 1
        assert node2.indegree == 1
        assert node2.outdegree == 0

        assert node1.successors == [node2]
        assert len(node1.predecessors) == 0
        assert node2.predecessors == [node1]
        assert len(node2.successors) == 0

    def test_node_connect_to(self):
        """Test connecting one node to another"""
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        self.add(node1, node2)

        self._check_single_connection(node1, node2)

    def test_node_connect_from(self):
        """Test connecting one node from another"""
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_from(node2)
        self.add(node1, node2)

        self._check_single_connection(node2, node1)

    def test_node_transmit(self):
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        info = models.Info(origin=node1, contents="foo")
        self.add(node1, node2, info)

        node1.transmit(info, node2)
        self.db.commit()

        transmission = info.transmissions[0]
        assert transmission.info_uuid == info.uuid
        assert transmission.origin_uuid == node1.uuid
        assert transmission.destination_uuid == node2.uuid

    @raises(ValueError)
    def test_node_transmit_no_connection(self):
        node1 = models.Node()
        node2 = models.Node()
        info = models.Info(origin=node1, contents="foo")
        self.add(node1, node2, info)

        node1.transmit(info, node2)
        self.db.commit()

    @raises(ValueError)
    def test_node_transmit_invalid_info(self):
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        info = models.Info(origin=node2, contents="foo")
        self.add(node1, node2, info)

        node1.transmit(info, node2)
        self.db.commit()

    def test_node_broadcast(self):
        node1 = models.Node()
        self.db.add(node1)

        for i in xrange(5):
            new_node = models.Node()
            node1.connect_to(new_node)
            self.db.add(new_node)

        info = models.Info(origin=node1, contents="foo")
        self.add(info)

        node1.broadcast(info)
        self.db.commit()

        transmissions = info.transmissions
        assert len(transmissions) == 5

    def test_node_outdegree(self):
        node1 = models.Node()
        self.db.add(node1)

        for i in xrange(5):
            assert node1.outdegree == i
            new_node = models.Node()
            node1.connect_to(new_node)
            self.add(new_node)

        assert node1.outdegree == 5

        node5 = self.db.query(models.Node).filter_by(outdegree=5).one()
        assert node5 == node1

    def test_node_indegree(self):
        node1 = models.Node()
        self.db.add(node1)

        for i in xrange(5):
            assert node1.indegree == i
            new_node = models.Node()
            node1.connect_from(new_node)
            self.add(new_node)

        assert node1.indegree == 5

        node5 = self.db.query(models.Node).filter_by(indegree=5).one()
        assert node5 == node1

    def test_node_has_connection_to(self):
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        self.add(node1, node2)

        assert node1.has_connection_to(node2)
        assert not node2.has_connection_to(node1)

    def test_node_has_connection_from(self):
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        self.add(node1, node2)

        assert not node1.has_connection_from(node2)
        assert node2.has_connection_from(node1)

    ##################################################################
    ## Vector
    ##################################################################

    def test_create_vector(self):
        """Test creating a vector between two nodes"""
        node1 = models.Node()
        node2 = models.Node()
        vector = models.Vector(origin=node1, destination=node2)
        self.add(node1, node2, vector)

        self._check_single_connection(node1, node2)
        assert len(vector.transmissions) == 0

    def test_create_bidirectional_vectors(self):
        """Test creating a bidirectional connection between nodes"""
        node1 = models.Node()
        node2 = models.Node()
        vector1 = models.Vector(origin=node1, destination=node2)
        vector2 = models.Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert vector1.origin_uuid == node1.uuid
        assert vector1.destination_uuid == node2.uuid
        assert vector2.origin_uuid == node2.uuid
        assert vector2.destination_uuid == node1.uuid

        assert node1.incoming_vectors == [vector2]
        assert node1.outgoing_vectors == [vector1]
        assert node2.incoming_vectors == [vector1]
        assert node2.outgoing_vectors == [vector2]

        assert node1.has_connection_to(node2)
        assert node1.has_connection_from(node2)
        assert node2.has_connection_to(node1)
        assert node2.has_connection_from(node1)

        assert node1.indegree == 1
        assert node2.indegree == 1
        assert node1.outdegree == 1
        assert node2.outdegree == 1

        assert len(vector1.transmissions) == 0
        assert len(vector2.transmissions) == 0

    def test_vector_repr(self):
        """Test the repr of a vector"""
        node1 = models.Node()
        node2 = models.Node()
        vector1 = models.Vector(origin=node1, destination=node2)
        vector2 = models.Vector(origin=node2, destination=node1)
        self.add(node1, node2, vector1, vector2)

        assert repr(vector1).split("-") == ["Vector", node1.uuid[:6], node2.uuid[:6]]
        assert repr(vector2).split("-") == ["Vector", node2.uuid[:6], node1.uuid[:6]]

    @raises(IntegrityError, FlushError)
    def test_create_duplicate_vector(self):
        """Check that creating the same vector twice throws an error"""
        node1 = models.Node()
        node2 = models.Node()
        vector1 = models.Vector(origin=node1, destination=node2)
        vector2 = models.Vector(origin=node1, destination=node2)
        self.add(node1, node2, vector1, vector2)

    ##################################################################
    ## Info
    ##################################################################

    def test_create_info(self):
        """Try creating an info"""
        node = models.Node()
        info = models.Info(origin=node, contents="foo")
        self.add(node, info)

        assert len(info.uuid) == 32
        assert info.type == "base"
        assert info.origin_uuid == node.uuid
        assert info.creation_time
        assert info.contents == "foo"
        assert len(info.transmissions) == 0

        assert node.information == [info]

    def test_create_two_infos(self):
        """Try creating two infos"""
        node = models.Node()
        info1 = models.Info(origin=node, contents="bar")
        info2 = models.Info(origin=node, contents="foo")
        self.add(node, info1, info2)

        assert info1.uuid != info2.uuid
        assert info1.origin_uuid == info2.origin_uuid
        assert info1.creation_time != info2.creation_time
        assert info1.contents != info2.contents
        assert len(info1.transmissions) == 0
        assert len(info2.transmissions) == 0

        assert len(node.information) == 2
        assert info1 in node.information
        assert info2 in node.information

    def test_info_repr(self):
        """Check the info repr"""
        node = models.Node()
        info = models.Info(origin=node)
        self.add(info)

        assert repr(info).split("-") == ["Info", info.uuid[:6], "base"]

    def test_info_copy_to(self):
        """Check that Info.copy_to works correctly"""
        node1 = models.Node()
        node2 = models.Node()
        node1.connect_to(node2)
        self.add(node1, node2)

        info1 = models.Info(origin=node1, contents="foo")
        node1.transmit(info1, node2)
        info2 = info1.copy_to(node2)
        self.add(info1, info2)

        assert info1.uuid != info2.uuid
        assert info1.type == info2.type
        assert info1.creation_time != info2.creation_time
        assert info1.contents == info2.contents
        assert info1.origin_uuid == node1.uuid
        assert info2.origin_uuid == node2.uuid
        assert len(info1.transmissions) == 1
        assert len(info2.transmissions) == 0
        assert node1.information == [info1]
        assert node2.information == [info2]

    ##################################################################
    ## Transmission
    ##################################################################

    def test_create_transmission(self):
        """Try creating a transmission"""
        node1 = models.Node()
        node2 = models.Node()
        vector = models.Vector(origin=node1, destination=node2)
        info = models.Info(origin=node1)
        transmission = models.Transmission(info=info, destination=node2)
        self.add(node1, node2, vector, info, transmission)

        assert len(transmission.uuid) == 32
        assert transmission.info_uuid == info.uuid
        assert transmission.origin_uuid == vector.origin_uuid
        assert transmission.destination_uuid == vector.destination_uuid
        assert transmission.transmit_time
        assert transmission.vector == vector
        assert vector.transmissions == [transmission]

    def test_transmission_repr(self):
        node1 = models.Node()
        node2 = models.Node()
        vector = models.Vector(origin=node1, destination=node2)
        info = models.Info(origin=node1)
        transmission = models.Transmission(info=info, destination=node2)
        self.add(node1, node2, vector, info, transmission)

        assert repr(transmission).split("-") == ["Transmission", transmission.uuid[:6]]

    def test_node_incoming_transmissions(self):
        node1 = models.Node()
        node2 = models.Node()
        node3 = models.Node()
        node1.connect_from(node2)
        node1.connect_from(node3)
        self.add(node1, node2, node3)

        info1 = models.Info(origin=node2, contents="foo")
        info2 = models.Info(origin=node3, contents="bar")
        self.add(info1, info2)

        node2.transmit(info1, node1)
        node3.transmit(info2, node1)
        self.db.commit()

        assert len(node1.incoming_transmissions) == 2
        assert len(node2.incoming_transmissions) == 0
        assert len(node3.incoming_transmissions) == 0

    def test_node_outgoing_transmissions(self):
        node1 = models.Node()
        node2 = models.Node()
        node3 = models.Node()
        node1.connect_to(node2)
        node1.connect_to(node3)
        self.add(node1, node2, node3)

        info1 = models.Info(origin=node1, contents="foo")
        info2 = models.Info(origin=node1, contents="bar")
        self.add(info1, info2)

        node1.transmit(info1, node2)
        node1.transmit(info2, node3)
        self.db.commit()

        assert len(node1.outgoing_transmissions) == 2
        assert len(node2.outgoing_transmissions) == 0
        assert len(node3.outgoing_transmissions) == 0
