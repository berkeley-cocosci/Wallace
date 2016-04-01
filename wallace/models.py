"""Define Wallace's core models."""

from datetime import datetime

from .db import Base

from sqlalchemy import ForeignKey, or_, and_
from sqlalchemy import Column, String, Text, Enum, Integer, Boolean, DateTime, Float
from sqlalchemy.orm import relationship, validates

import inspect

DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%f"


def timenow():
    """A string representing the current date and time."""
    return datetime.now()


class SharedMixin(object):
    """Create shared columns."""

    id = Column(Integer, primary_key=True, index=True)

    creation_time = Column(DateTime, nullable=False, default=timenow)

    property1 = Column(String(26), nullable=True, default=None)
    property2 = Column(String(26), nullable=True, default=None)
    property3 = Column(String(26), nullable=True, default=None)
    property4 = Column(String(26), nullable=True, default=None)
    property5 = Column(String(26), nullable=True, default=None)


class Participant(Base, SharedMixin):

    """An ex silico participant."""

    __tablename__ = "participant"

    # the participant type -- this allows for inheritance
    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'participant'
    }

    worker_id = Column(String(50), nullable=False)
    assignment_id = Column(String(50), nullable=False, index=True)
    unique_id = Column(String(50), nullable=False, index=True)
    hit_id = Column(String(50), nullable=False)

    end_time = Column(DateTime)

    base_pay = Column(Float)
    bonus = Column(Float)

    status = Column(Enum("working", "submitted", "approved", "rejected", "returned", "abandoned", "did_not_attend", "bad_data", "missing_notification", name="participant_status"),
                    nullable=False, default="working", index=True)

    def __init__(self, worker_id, assignment_id, hit_id):

        self.worker_id = worker_id
        self.assignment_id = assignment_id
        self.hit_id = hit_id
        self.unique_id = worker_id + ":" + assignment_id


class Network(Base, SharedMixin):

    """A collection of Nodes and Vectors."""

    __tablename__ = "network"

    # the network type -- this allows for inheritance
    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'base'
    }

    # how big the network can get, this number is used by the full()
    # method to decide whether the network is full
    max_size = Column(Integer, nullable=False, default=1e6)

    # whether the network is currently full
    full = Column(Boolean, nullable=False, default=False, index=True)

    # the role of the network, by default wallace initializes all
    # networks as either "practice" or "experiment"
    role = Column(String(26), nullable=False, default="default", index=True)

    def __len__(self):
        """The size of a network is undefined.

        The length of a network is confusing because it might refer either
        to the number of agents, sources, or nodes. Better to be explicit.
        """
        raise SyntaxError(
            "len is not defined for networks. " +
            "Use len(net.nodes()) instead.")

    def __repr__(self):
        """The string representation of a network."""
        return ("<Network-{}-{} with {} nodes, {} vectors, {} infos, "
                "{} transmissions and {} transformations>").format(
            self.id,
            self.type,
            len(self.nodes()),
            len(self.vectors()),
            len(self.infos()),
            len(self.transmissions()),
            len(self.transformations()))

    """ ###################################
    Methods that get things about a Network
    ################################### """

    def nodes(self, type=None, failed=False, participant_id=None):
        """
        Get nodes in the network.

        type specifies the type of Node. Failed can be "all", False
        (default) or True. If a participant_id is passed only
        nodes with that participant_id will be returned.
        """
        if type is None:
            type = Node

        if not issubclass(type, Node):
            raise(TypeError("{} is not a valid node type.".format(type)))

        if failed not in ["all", False, True]:
            raise ValueError("{} is not a valid node failed".format(failed))

        if participant_id is not None:
            if failed == "all":
                return type\
                    .query\
                    .filter_by(network_id=self.id,
                               participant_id=participant_id)\
                    .all()
            else:
                return type\
                    .query\
                    .filter_by(network_id=self.id,
                               participant_id=participant_id,
                               failed=failed)\
                    .all()
        else:
            if failed == "all":
                return type\
                    .query\
                    .filter_by(network_id=self.id)\
                    .all()
            else:
                return type\
                    .query\
                    .filter_by(failed=failed, network_id=self.id)\
                    .all()

    def size(self, type=None, failed=False):
        if type is None:
            type = Node

        if not issubclass(type, Node):
            raise(TypeError("{} is not a valid node type.".format(type)))

        if failed not in ["all", False, True]:
            raise ValueError("{} is not a valid node failed".format(failed))

        if failed == "all":
            return len(type.query
                       .with_entities(type.id)
                       .filter_by(network_id=self.id)
                       .all())
        else:
            return len(type.query
                       .with_entities(type.id)
                       .filter_by(network_id=self.id, failed=failed)
                       .all())

    def infos(self, type=None, failed=False):
        """
        Get infos in the network.

        type specifies the type of info (defaults to Info). failed { False,
        True, "all" } specifies the failed state of the infos. To get infos
        from a specific node, see the infos() method in class Node.
        """
        if type is None:
            type = Info
        if failed not in ["all", False, True]:
            raise ValueError("{} is not a valid failed".format(failed))

        if failed == "all":
            return type.query\
                .filter_by(network_id=self.id)\
                .all()
        else:
            return type.query.filter_by(
                network_id=self.id, failed=failed).all()

    def transmissions(self, status="all", failed=False):
        """
        Get transmissions in the network.

        status { "all", "received", "pending" }
        failed { False, True, "all" }
        To get transmissions from a specific vector, see the
        transmissions() method in class Vector.
        """
        if status not in ["all", "pending", "received"]:
            raise(ValueError("You cannot get transmission of status {}.".format(status) +
                  "Status can only be pending, received or all"))
        if failed not in ["all", False, True]:
            raise ValueError("{} is not a valid failed".format(failed))

        if status == "all":
            if failed == "all":
                return Transmission.query\
                    .filter_by(network_id=self.id)\
                    .all()
            else:
                return Transmission.query\
                    .filter_by(network_id=self.id, failed=failed)\
                    .all()
        else:
            if failed == "all":
                return Transmission.query\
                    .filter_by(network_id=self.id, status=status)\
                    .all()
            else:
                return Transmission.query\
                    .filter_by(network_id=self.id, status=status, failed=failed)\
                    .all()

    def transformations(self, type=None, failed=False):
        """
        Get transformations in the network.

        type specifies the type of transformation (default = Transformation).
        failed = { False, True, "all" }

        To get transformations from a specific node,
        see Node.transformations().
        """
        if type is None:
            type = Transformation

        if failed not in ["all", True, False]:
            raise ValueError("{} is not a valid failed".format(failed))

        if failed == "all":
            return type.query\
                .filter_by(network_id=self.id)\
                .all()
        else:
            return type.query\
                .filter_by(network_id=self.id, failed=failed)\
                .all()

    def latest_transmission_recipient(self):
        """Get the node that most recently received a transmission."""
        from operator import attrgetter

        ts = Transmission.query\
            .filter_by(status="received", network_id=self.id, failed=False)\
            .all()

        if ts:
            t = max(ts, key=attrgetter('receive_time'))
            return t.destination
        else:
            return None

    def vectors(self, failed=False):
        """
        Get vectors in the network.

        failed = { False, True, "all" }
        To get the vectors to/from to a specific node, see Node.vectors().
        """
        if failed not in ["all", False, True]:
            raise ValueError("{} is not a valid vector failed".format(failed))

        if failed == "all":
            return Vector.query\
                .filter_by(network_id=self.id)\
                .all()
        else:
            return Vector.query\
                .filter_by(network_id=self.id, failed=failed)\
                .all()

    """ ###################################
    Methods that make Networks do things
    ################################### """

    def calculate_full(self):
        """Set whether the network is full."""
        self.full = len(self.nodes()) >= self.max_size

    def print_verbose(self):
        """Print a verbose representation of a network."""
        print "Nodes: "
        for a in (self.nodes(failed="all")):
            print a

        print "\nVectors: "
        for v in (self.vectors(failed="all")):
            print v

        print "\nInfos: "
        for i in (self.infos(failed="all")):
            print i

        print "\nTransmissions: "
        for t in (self.transmissions(failed="all")):
            print t

        print "\nTransformations: "
        for t in (self.transformations(failed="all")):
            print t


class Node(Base, SharedMixin):
    """A point in a network."""

    __tablename__ = "node"

    # the node type -- this allows for inheritance
    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'base'
    }

    # the network that this node is a part of
    network_id = Column(Integer, ForeignKey('network.id'), index=True)
    network = relationship(Network, backref="all_nodes")

    # whether the node has failed
    failed = Column(Boolean, nullable=False, default=False, index=True)

    # the time when the node changed from alive->dead or alive->failed
    time_of_death = Column(DateTime, default=None)

    # the participant id is the sha512 hash of the psiTurk uniqueId of the
    # participant who was this node.
    participant_id = Column(String(128), default=None, index=True)

    def __repr__(self):
        """The string representation of a node."""
        return "Node-{}-{}".format(self.id, self.type)

    def __json__(self):
        return {
            "id": self.id,
            "type": self.type,
            "network_id": self.network_id,
            "creation_time": self.creation_time,
            "time_of_death": self.time_of_death,
            "failed": self.failed,
            "participant_id": self.participant_id,
            "property1": self.property1,
            "property2": self.property2,
            "property3": self.property3,
            "property4": self.property4,
            "property5": self.property5
        }

    """ ###################################
    Methods that get things about a node
    ################################### """

    def vectors(self, direction="all"):
        """
        Get vectors that connect at this node.

        Direction can be "incoming", "outgoing" or "all" (default).
        """
        # check direction
        if direction not in ["all", "incoming", "outgoing"]:
            raise ValueError(
                "{} is not a valid vector direction. "
                "Must be all, incoming or outgoing.".format(direction))

        # get the vectors
        if direction == "all":
            return Vector.query\
                .filter(and_(Vector.failed == False,
                        or_(Vector.destination_id == self.id,
                            Vector.origin_id == self.id)))\
                .all()

        if direction == "incoming":
            return Vector.query\
                .filter_by(destination_id=self.id, failed=False)\
                .all()

        if direction == "outgoing":
            return Vector.query\
                .filter_by(origin_id=self.id, failed=False)\
                .all()

    def neighbors(self, type=None, connection="to"):
        """
        Get a node's neighbors - nodes that are directly connected to it.

        Type specifies the class of neighbour and must be a subclass of
        Node (default is Node).
        Connection is the direction of the connections and can be "to"
        (default), "from", "either", or "both".
        """
        # get type
        if type is None:
            type = Node
        if not issubclass(type, Node):
            raise ValueError("{} is not a valid neighbor type, \
                    needs to be a subclass of Node.".format(type))

        # get connection
        if connection not in ["both", "either", "from", "to"]:
            raise ValueError("{} not a valid neighbor connection. \
                Should be both, either, to or from.".format(connection))

        neighbors = []
        # get the neighbours
        if connection == "to":
            outgoing_vectors = Vector.query\
                .with_entities(Vector.destination_id)\
                .filter_by(origin_id=self.id, failed=False).all()

            neighbor_ids = [v.destination_id for v in outgoing_vectors]
            if neighbor_ids:
                neighbors = Node.query.filter(Node.id.in_(neighbor_ids)).all()
                neighbors = [n for n in neighbors if isinstance(n, type)]

        if connection == "from":
            incoming_vectors = Vector.query.with_entities(Vector.origin_id)\
                .filter_by(destination_id=self.id, failed=False).all()

            neighbor_ids = [v.origin_id for v in incoming_vectors]
            if neighbor_ids:
                neighbors = Node.query.filter(Node.id.in_(neighbor_ids)).all()
                neighbors = [n for n in neighbors if isinstance(n, type)]

        if connection == "either":
            neighbors = list(set(self.neighbors(type=type, connection="to") +
                                 self.neighbors(type=type, connection="from")))

        if connection == "both":
            neighbors = list(set(self.neighbors(type=type, connection="to")) &
                             set(self.neighbors(type=type, connection="from")))

        return neighbors

    def is_connected(self, whom, direction="to"):
        """
        Check whether this node is connected [to/from] whom.

        whom can be a list of nodes or a single node.
        direction can be "to" (default), "from", "both" or "either".

        If whom is a single node this method returns a boolean,
        otherwise it returns a list of booleans
        """
        # make whom a list
        if isinstance(whom, list):
            is_list = True
        else:
            whom = [whom]
            is_list = False

        whom_ids = [n.id for n in whom]

        # check whom contains only Nodes
        for node in whom:
            if not isinstance(node, Node):
                raise TypeError("is_connected cannot parse objects of type {}."
                                .format(type(node)))

        # check direction
        if direction not in ["to", "from", "either", "both"]:
            raise ValueError("{} is not a valid direction for is_connected"
                             .format(direction))

        # get is_connected
        connected = []
        if direction == "to":
            vectors = Vector.query.with_entities(Vector.destination_id)\
                .filter_by(origin_id=self.id, failed=False).all()
            destinations = set([v.destination_id for v in vectors])
            for w in whom_ids:
                connected.append(w in destinations)

        elif direction == "from":
            vectors = Vector.query.with_entities(Vector.origin_id)\
                .filter_by(destination_id=self.id, failed=False).all()
            origins = set([v.origin_id for v in vectors])
            for w in whom_ids:
                connected.append(w in origins)

        elif direction in ["either", "both"]:

            vectors = Vector.query\
                .with_entities(Vector.origin_id, Vector.destination_id)\
                .filter(and_(Vector.failed == False,
                             or_(Vector.destination_id == self.id,
                                 Vector.origin_id == self.id))).all()

            destinations = set([v.destination_id for v in vectors])
            origins = set([v.origin_id for v in vectors])

            if direction == "either":
                origins_destinations = destinations.union(origins)

            elif direction == "both":
                origins_destinations = destinations.intersection(origins)

            for w in whom_ids:
                connected.append(w in origins_destinations)

        if is_list:
            return connected
        else:
            return connected[0]

    def infos(self, type=None):
        """
        Get infos that originate from this node.
        Type must be a subclass of info, the default is Info.
        """
        if type is None:
            type = Info

        if not issubclass(type, Info):
            raise(TypeError("Cannot get-info of type {} as it is not a valid type."
                            .format(type)))

        return type\
            .query\
            .filter_by(origin_id=self.id, failed=False)\
            .all()

    def received_infos(self, type=None):
        """
        Get infos that have been sent to this node.
        Type must be a subclass of info, the default is Info.
        """
        if type is None:
            type = Info

        if not issubclass(type, Info):
            raise(TypeError("Cannot get infos of type {} as it is not a valid type."
                            .format(type)))

        transmissions = Transmission\
            .query.with_entities(Transmission.info_id)\
            .filter_by(destination_id=self.id, status="received", failed=False).all()

        info_ids = [t.info_id for t in transmissions]
        if info_ids:
            return type.query.filter(type.id.in_(info_ids)).all()
        else:
            return []

    def transmissions(self, direction="outgoing", status="all"):
        """
        Get transmissions sent to or from this node.

        Direction can be "all", "incoming" or "outgoing" (default).
        Status can be "all" (default), "pending", or "received".
        """
        #check parameters
        if direction not in ["incoming", "outgoing", "all"]:
            raise(ValueError("You cannot get transmissions of direction {}."
                             .format(direction) +
                  "Type can only be incoming, outgoing or all."))

        if status not in ["all", "pending", "received"]:
            raise(ValueError("You cannot get transmission of status {}."
                             .format(status) +
                  "Status can only be pending, received or all"))

        # get transmissions
        if direction == "all":
            if status == "all":
                return Transmission.query\
                    .filter(and_(Transmission.failed == False,
                                 or_(Transmission.destination_id == self.id,
                                     Transmission.origin_id == self.id)))\
                    .all()
            else:
                return Transmission.query\
                    .filter(and_(Transmission.failed == False,
                                 Transmission.status == status,
                                 or_(Transmission.destination_id == self.id,
                                     Transmission.origin_id == self.id)))\
                    .all()
        if direction == "incoming":
            if status == "all":
                return Transmission.query\
                    .filter_by(failed=False, destination_id=self.id)\
                    .all()
            else:
                return Transmission.query\
                    .filter(and_(Transmission.failed == False,
                                 Transmission.destination_id == self.id,
                                 Transmission.status == status))\
                    .all()
        if direction == "outgoing":
            if status == "all":
                return Transmission.query\
                    .filter_by(failed=False, origin_id=self.id)\
                    .all()
            else:
                return Transmission.query\
                    .filter(and_(Transmission.failed == False,
                                 Transmission.origin_id == self.id,
                                 Transmission.status == status))\
                    .all()

    def transformations(self, type=None):
        """
        Get Transformations done by this Node.

        type must be a type of Transformation (defaults to Transformation)
        """
        if type is None:
            type = Transformation
        return type\
            .query\
            .filter_by(node_id=self.id, failed=False)\
            .all()

    """ ###################################
    Methods that make nodes do things
    ################################### """

    def fail(self, vectors=True, infos=True, transmissions=True, transformations=True):
        """
        Fail a node, setting its status to "failed".

        Also fails all vectors that connect to or from the node.
        You cannot fail a node that has already failed, but you
        can fail a dead node.
        """
        if self.failed is True:
            raise AttributeError(
                "Cannot fail {} - it has already failed.".format(self))
        else:
            self.failed = True
            self.time_of_death = timenow()
            if self.network is not None:
                self.network.calculate_full()

            if vectors:
                for v in self.vectors():
                    v.fail()
            if infos:
                for i in self.infos():
                    i.fail()
            if transmissions:
                for t in self.transmissions(direction="all"):
                    t.fail()
            if transformations:
                for t in self.transformations():
                    t.fail()

    def connect(self, whom, direction="to"):
        """Create a vector from self to/from whom.

        whom may be a (nested) list of nodes.
        Will raise an error if:
            (1) whom is not a node or list of nodes
            (2) whom is/contains a source if direction
                is to or both
            (3) whom is/contains self
            (4) whom is/contains a node in a different
                network
        If self is already connected to/from whom a Warning
        is raised and nothing happens.

        This method returns a list of the vectors created
        (even if there is only one).
        """

        # check direction
        if direction not in ["to", "from", "both"]:
            raise ValueError("{} is not a valid direction for connect()".format(direction))

        # make whom a list
        whom = self.flatten([whom])

        # make the connections
        new_vectors = []
        if direction in ["to", "both"]:
            already_connected_to = self.flatten([self.is_connected(direction="to", whom=whom)])
            for node, connected in zip(whom, already_connected_to):
                if connected:
                    print("Warning! {} already connected to {}, instruction to connect will be ignored."
                          .format(self, node))
                else:
                    new_vectors.append(Vector(origin=self, destination=node))
        if direction in ["from", "both"]:
            already_connected_from = self.flatten([self.is_connected(direction="from", whom=whom)])
            for node, connected in zip(whom, already_connected_from):
                if connected:
                    print("Warning! {} already connected from {}, instruction to connect will be ignored."
                          .format(self, node))
                else:
                    new_vectors.append(Vector(origin=node, destination=self))
        return new_vectors

    def flatten(self, l):
        if l == []:
            return l
        if isinstance(l[0], list):
            return self.flatten(l[0]) + self.flatten(l[1:])
        return l[:1] + self.flatten(l[1:])

    def transmit(self, what=None, to_whom=None):
        """
        Transmit one or more infos from one node to another.

        "what" dictates which infos are sent, it can be:
            (1) None (in which case the node's _what method is called).
            (2) an Info (in which case the node transmits the info)
            (3) a subclass of Info (in which case the node transmits all its infos of that type)
            (4) a list of any combination of the above
        "to_whom" dictates which node(s) the infos are sent to, it can be:
            (1) None (in which case the node's _to_whom method is called)
            (2) a Node (in which case the node transmits to that node)
            (3) a subclass of Node (in which case the node transmits to all nodes of that type it is connected to)
            (4) a list of any combination of the above
        Will additionally raise an error if:
            (1) _what() or _to_whom() returns None or a list containing None.
            (2) what is/contains an info that does not originate from the transmitting node
            (3) to_whom is/contains a node that the transmitting node does have have a live connection with.
        """

        # make the list of what
        what = self.flatten([what])
        for i in range(len(what)):
            if what[i] is None:
                what[i] = self._what()
            elif inspect.isclass(what[i]) and issubclass(what[i], Info):
                what[i] = self.infos(type=what[i])
        what = self.flatten(what)
        for i in range(len(what)):
            if inspect.isclass(what[i]) and issubclass(what[i], Info):
                what[i] = self.infos(type=what[i])
        what = list(set(self.flatten(what)))

        # make the list of to_whom
        to_whom = self.flatten([to_whom])
        for i in range(len(to_whom)):
            if to_whom[i] is None:
                to_whom[i] = self._to_whom()
            elif inspect.isclass(to_whom[i]) and issubclass(to_whom[i], Node):
                to_whom[i] = self.neighbors(connection="to", type=to_whom[i])
        to_whom = self.flatten(to_whom)
        for i in range(len(to_whom)):
            if inspect.isclass(to_whom[i]) and issubclass(to_whom[i], Node):
                to_whom[i] = self.neighbors(connection="to", type=to_whom[i])
        to_whom = list(set(self.flatten(to_whom)))

        transmissions = []
        vectors = self.vectors(direction="outgoing")
        for w in what:
            for tw in to_whom:
                try:
                    vector = [v for v in vectors
                              if v.destination_id == tw.id][0]
                except:
                    raise ValueError("{} cannot transmit to {} as it does not have \
                                      a connection to them".format(self, tw))
                t = Transmission(info=w, vector=vector)
                transmissions.append(t)
        if len(transmissions) == 1:
            return transmissions[0]
        else:
            return transmissions

    def _what(self):
        return Info

    def _to_whom(self):
        return Node

    def receive(self, what=None):
        """
        Mark transmissions as received, then pass their infos to update().

        "what" can be:
            (1) None (the default) in which case all pending transmissions are received
            (2) a specific transmission.
        Will raise an error if the node is told to receive a transmission it has not been sent.
        """

        # check self is not failed
        if self.failed:
            raise ValueError("{} cannot receive as it has failed.".format(self))

        received_transmissions = []
        if what is None:
            pending_transmissions = self.transmissions(direction="incoming", status="pending")
            for transmission in pending_transmissions:
                transmission.status = "received"
                transmission.receive_time = timenow()
                received_transmissions.append(transmission)

        elif isinstance(what, Transmission):
            if what in self.transmissions(direction="incoming", status="pending"):
                transmission.status = "received"
                what.receive_time = timenow()
                received_transmissions.append(what)
            else:
                raise(ValueError("{} cannot receive {} as it is not in its pending_transmissions"
                                 .format(self, what)))
        else:
            raise ValueError("Nodes cannot receive {}".format(what))

        self.update([t.info for t in received_transmissions])

    def update(self, infos):
        """
        Update controls the default behavior of a node when it receives infos.
        By default it does nothing.
        """
        # check self is not failed
        if self.failed:
            raise ValueError("{} cannot update as it has failed.".format(self))

    def replicate(self, info_in):
        # check self is not failed
        if self.failed:
            raise ValueError("{} cannot replicate as it has failed.".format(self))

        from transformations import Replication
        info_out = type(info_in)(origin=self, contents=info_in.contents)
        Replication(info_in=info_in, info_out=info_out)

    def mutate(self, info_in):
        # check self is not failed
        if self.failed:
            raise ValueError("{} cannot mutate as it has failed.".format(self))

        from transformations import Mutation
        info_out = type(info_in)(origin=self, contents=info_in._mutated_contents())
        Mutation(info_in=info_in, info_out=info_out)


class Vector(Base, SharedMixin):

    """
    A Vector is a path that links two Nodes.
    Nodes can only send each other information if they are linked by a Vector.
    """

    """ ###################################
    SQLAlchemy stuff. Touch at your peril!
    ################################### """

    __tablename__ = "vector"

    # the origin node
    origin_id = Column(Integer, ForeignKey('node.id'), index=True)
    origin = relationship(Node, foreign_keys=[origin_id],
                          backref="all_outgoing_vectors")

    # the destination node
    destination_id = Column(Integer, ForeignKey('node.id'), index=True)
    destination = relationship(Node, foreign_keys=[destination_id],
                               backref="all_incoming_vectors")

    # the network that this vector is in
    network_id = Column(Integer, ForeignKey('network.id'), index=True)
    network = relationship(Network, backref="all_vectors")

    # whether the vector has failed
    failed = Column(Boolean, nullable=False, default=False, index=True)

    # the time when the vector changed from alive->dead
    time_of_death = Column(DateTime, default=None)

    def __init__(self, origin, destination):

        # check origin and destination are in the same network
        if origin.network_id != destination.network_id:
            raise ValueError("{}, in network {}, cannot connect with {} as it is in network {}"
                             .format(origin, origin.network_id, destination, destination.network_id))

        # check neither the origin or destination have failed
        if origin.failed:
            raise ValueError("{} cannot connect to {} as {} has failed".format(origin, destination, origin))
        if destination.failed:
            raise ValueError("{} cannot connect to {} as {} has failed".format(origin, destination, destination))

        # check the destination isnt a source
        from wallace.nodes import Source
        if isinstance(destination, Source):
            raise(TypeError("Cannot connect to {} as it is a Source.".format(destination)))

        # check origin and destination are different nodes
        if origin == destination:
            raise ValueError("{} cannot connect to itself.".format(origin))

        self.origin = origin
        self.origin_id = origin.id
        self.destination = destination
        self.destination_id = destination.id
        self.network = origin.network
        self.network_id = origin.network_id

    def __repr__(self):
        """The string representation of a vector."""
        return "Vector-{}-{}".format(
            self.origin_id, self.destination_id)

    def __json__(self):
        return {
            "id": self.id,
            "origin_id": self.origin_id,
            "destination_id": self.destination_id,
            "info_id": self.info_id,
            "network_id": self.network_id,
            "creation_time": self.creation_time,
            "failed": self.failed,
            "time_of_death": self.time_of_death,
            "property1": self.property1,
            "property2": self.property2,
            "property3": self.property3,
            "property4": self.property4,
            "property5": self.property5
        }

    ###################################
    # Methods that get things about a Vector
    ###################################

    def transmissions(self, status="all"):
        """
        Get transmissions sent along this Vector.
        Status can be "all" (the default), "pending", or "received".
        """

        if status not in ["all", "pending", "received"]:
            raise(ValueError("You cannot get {} transmissions.".format(status) +
                  "Status can only be pending, received or all"))

        if status == "all":
            return Transmission\
                .query\
                .filter_by(vector_id=self.id,
                           failed=False)\
                .all()
        else:
            return Transmission\
                .query\
                .filter_by(vector_id=self.id,
                           status=status,
                           failed=False)\
                .all()

    ###################################
    # Methods that make Vectors do things
    ###################################

    def fail(self):
        if self.failed is True:
            raise AttributeError("You cannot fail {}, it has already failed".format(self))
        else:
            self.failed = True
            self.time_of_death = timenow()


class Info(Base, SharedMixin):

    """A unit of information sent along a vector via a transmission."""

    __tablename__ = "info"

    # the info type -- this allows for inheritance
    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'base'
    }

    # the node that created this info
    origin_id = Column(Integer, ForeignKey('node.id'), index=True)
    origin = relationship(Node, backref='all_infos')

    # the network the info is in
    network_id = Column(Integer, ForeignKey('network.id'), index=True)
    network = relationship(Network, backref="all_infos")

    # whether the info has failed
    failed = Column(Boolean, nullable=False, default=False, index=True)

    # the time when the info failed
    time_of_death = Column(DateTime, default=None)

    # the contents of the info
    contents = Column(Text(), default=None)

    def __init__(self, origin, contents=None):
        self.origin = origin
        self.origin_id = origin.id
        self.contents = contents
        self.network_id = origin.network_id
        self.network = origin.network

    @validates("contents")
    def _write_once(self, key, value):
        existing = getattr(self, key)
        if existing is not None:
            raise ValueError("The contents of an info is write-once.")
        return value

    def __repr__(self):
        """The string representation of an info."""
        return "Info-{}-{}".format(self.id, self.type)

    def __json__(self):
        return {
            "id": self.id,
            "type": self.type,
            "origin_id": self.origin_id,
            "network_id": self.network_id,
            "creation_time": self.creation_time,
            "failed": self.failed,
            "time_of_death": self.time_of_death,
            "contents": self.contents,
            "property1": self.property1,
            "property2": self.property2,
            "property3": self.property3,
            "property4": self.property4,
            "property5": self.property5
        }

    def fail(self):
        if self.failed is True:
            raise AttributeError("Cannot fail {} - it has already failed.".format(self))
        else:
            self.failed = True
            self.time_of_death = timenow()

    def transmissions(self, status="all"):
        if status not in ["all", "pending", "received"]:
            raise(ValueError("You cannot get transmission of status {}.".format(status) +
                             "Status can only be pending, received or all"))
        if status == "all":
            return Transmission\
                .query\
                .filter_by(info_id=self.id,
                           failed=False)\
                .all()
        else:
            return Transmission\
                .query\
                .filterby(info_id=self.id,
                          status=status,
                          failed=False)\
                .all()

    def transformations(self, relationship="all"):
        if relationship not in ["all", "parent", "child"]:
            raise(ValueError("You cannot get transformations of relationship {}"
                             .format(relationship) +
                  "Relationship can only be parent, child or all."))

        if relationship == "all":
            return Transformation\
                .query\
                .filter(and_(Transformation.failed == False,
                             or_(Transformation.info_in == self,
                                 Transformation.info_out == self)))\
                .all()

        if relationship == "parent":
            return Transformation\
                .query\
                .filter_by(info_in_id=self.id,
                           failed=False)\
                .all()

        if relationship == "child":
            return Transformation\
                .query\
                .filter_by(info_out_id=self.id,
                           failed=False)\
                .all()

    def _mutated_contents(self):
        raise NotImplementedError("_mutated_contents needs to be overwritten in class {}"
                                  .format(type(self)))


class Transmission(Base, SharedMixin):
    """
    A Transmission is when an Info is sent along a Vector.
    """

    __tablename__ = "transmission"

    # the vector the transmission passed along
    vector_id = Column(Integer, ForeignKey('vector.id'), index=True)
    vector = relationship(Vector, backref='all_transmissions')

    # the info that was transmitted
    info_id = Column(Integer, ForeignKey('info.id'), index=True)
    info = relationship(Info, backref='all_transmissions')

    # the origin node
    origin_id = Column(Integer, ForeignKey('node.id'), index=True)
    origin = relationship(Node, foreign_keys=[origin_id],
                          backref="all_outgoing_transmissions")

    # the destination node
    destination_id = Column(Integer, ForeignKey('node.id'), index=True)
    destination = relationship(Node, foreign_keys=[destination_id],
                               backref="all_incoming_transmissions")

    # the network of the transformation
    network_id = Column(Integer, ForeignKey('network.id'), index=True)
    network = relationship(Network, backref="networks_transmissions")

    # the time at which the transmission was received
    receive_time = Column(DateTime, default=None)

    # whether the transmission has failed
    failed = Column(Boolean, nullable=False, default=False, index=True)

    # the time when the transmission failed
    time_of_death = Column(DateTime, default=None)

    # the status of the transmission, can be pending or received
    status = Column(Enum("pending", "received", name="transmission_status"),
                    nullable=False, default="pending", index=True)

    def __init__(self, vector, info):

        # check vector is not failed
        if vector.failed:
            raise ValueError("Cannot transmit along {} as it has failed.".format(vector))

        # check the origin of the vector is the same as the origin of the info
        if info.origin_id != vector.origin_id:
            raise ValueError("Cannot transmit {} along {} as they do not have the same origin".format(info, vector))

        self.vector_id = vector.id
        self.vector = vector
        self.info_id = info
        self.info = info
        self.origin_id = vector.origin_id
        self.origin = vector.origin
        self.destination_id = vector.destination_id
        self.destination = vector.destination
        self.network_id = vector.network_id
        self.network = vector.network

    def mark_received(self):
        self.receive_time = timenow()
        self.status = "received"

    def __repr__(self):
        """The string representation of a transmission."""
        return "Transmission-{}".format(self.id)

    def __json__(self):
        return {
            "id": self.id,
            "vector_id": self.vector_id,
            "origin_id": self.origin_id,
            "destination_id": self.destination_id,
            "info_id": self.info_id,
            "network_id": self.network_id,
            "creation_time": self.creation_time,
            "receive_time": self.receive_time,
            "failed": self.failed,
            "time_of_death": self.time_of_death,
            "status": self.status,
            "property1": self.property1,
            "property2": self.property2,
            "property3": self.property3,
            "property4": self.property4,
            "property5": self.property5
        }

    def fail(self):
        if self.failed is True:
            raise AttributeError("Cannot fail {} - it has already failed."
                                 .format(self))
        else:
            self.failed = True
            self.time_of_death = timenow()


class Transformation(Base, SharedMixin):
    """
    A Transformation is when one info is used to generate another Info.
    """

    __tablename__ = "transformation"

    # the transformation type -- this allows for inheritance
    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'base'
    }

    # the info before it was transformed
    info_in_id = Column(Integer, ForeignKey('info.id'), index=True)
    info_in = relationship(Info, foreign_keys=[info_in_id],
                           backref="transformation_applied_to")

    # the info produced as a result of the transformation
    info_out_id = Column(Integer, ForeignKey('info.id'), index=True)
    info_out = relationship(Info, foreign_keys=[info_out_id],
                            backref="transformation_whence")

    node_id = Column(Integer, ForeignKey('node.id'), index=True)
    node = relationship(Node, backref='transformations_here')

    # the network of the transformation
    network_id = Column(Integer, ForeignKey('network.id'), index=True)
    network = relationship(Network, backref="networks_transformations")

    # whether the transformation has failed
    failed = Column(Boolean, nullable=False, default=False, index=True)

    # the time when the transformation failed
    time_of_death = Column(DateTime, default=None)

    def __repr__(self):
        """The string representation of a transformation."""
        return "Transformation-{}".format(self.id)

    def __init__(self, info_in, info_out):

        # check info_in is from the same node as info_out or has been sent to the same node
        if (info_in.origin_id != info_out.origin_id and
           info_in.id not in [t.info_id for t in info_out.origin.transmissions(direction="incoming", status="received")]):
            raise ValueError("Cannot transform {} into {} as they are not at the same node."
                             .format(info_in, info_out))

        self.info_in = info_in
        self.info_out = info_out
        self.node = info_out.origin
        self.network = info_out.network
        self.info_in_id = info_in.id
        self.info_out_id = info_out.id
        self.node_id = info_out.origin_id
        self.network_id = info_out.network_id

    def __json__(self):
        return {
            "id": self.id,
            "info_in_id": self.info_in_id,
            "info_out_id": self.info_out_id,
            "node_id": self.node_id,
            "network_id": self.network_id,
            "creation_time": self.creation_time,
            "failed": self.failed,
            "time_of_death": self.time_of_death,
            "property1": self.property1,
            "property2": self.property2,
            "property3": self.property3,
            "property4": self.property4,
            "property5": self.property5
        }

    def fail(self):
        if self.failed is True:
            raise AttributeError(
                "Cannot fail {} - it has already failed.".format(self))
        else:
            self.failed = True
            self.time_of_death = timenow()


class Notification(Base, SharedMixin):

    __tablename__ = "notification"

    # the assignment is from AWS the notification pertains to
    assignment_id = Column(String, nullable=False)

    # the type of notification
    event_type = Column(String, nullable=False)
