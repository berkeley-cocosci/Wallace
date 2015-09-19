from wallace import networks, nodes, db, models
import random
from nose.tools import assert_raises


class TestNetworks(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def test_create_network(self):
        net = models.Network()
        assert isinstance(net, models.Network)

    def test_node_failure(self):
        net = networks.Network()
        for _ in range(5):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add(agent)
        agent = None
        source = nodes.Source()
        self.db.add(source)
        net.add(source)
        self.db.commit()

        assert len(net.nodes(type=nodes.Agent)) == 5

        random.choice(net.nodes(type=nodes.Agent)).fail()

        assert len(net.nodes(type=nodes.Agent)) == 4
        assert len(net.nodes(type=nodes.Agent, failed="all")) == 5
        assert len(net.nodes()) == 5
        assert len(net.nodes(failed="all")) == 6
        assert len(net.nodes(failed=True)) == 1

    def test_network_agents(self):
        net = networks.Network()
        assert len(net.nodes(type=nodes.Agent)) == 0

        agent = nodes.Agent()
        self.db.add(agent)

        net.add(agent)

        self.db.commit()

        assert net.nodes(type=nodes.Agent) == [agent]
        assert isinstance(net, models.Network)

    def test_network_sources(self):
        net = networks.Network()

        assert len(net.nodes(type=nodes.Source)) == 0

        source = nodes.Source()
        net.add(source)
        self.db.add(source)
        self.db.commit()

        assert net.nodes(type=nodes.Source) == [source]

    def test_network_nodes(self):
        net = models.Network()
        self.db.add(net)
        self.db.commit()

        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        agent1 = nodes.Agent(network=net)
        agent2 = nodes.Agent(network=net)
        agent3 = nodes.Agent(network=net)

        assert set([node1, node2, agent1, agent2, agent3]) == set(net.nodes())
        assert set([agent1, agent2, agent3]) == set(net.nodes(type=nodes.Agent))

        node1.fail()
        agent1.fail()

        assert set(net.nodes()) == set([node2, agent2, agent3])
        assert set(net.nodes(failed="all")) == set([node1, node2, agent1, agent2, agent3])
        assert set(net.nodes(failed=True)) == set([node1, agent1])
        assert set(net.nodes(type=nodes.Agent, failed="all")) == set([agent1, agent2, agent3])

    def test_network_vectors(self):
        net = networks.Network()

        assert len(net.vectors()) == 0

        agent1 = nodes.Agent()
        agent2 = nodes.Agent()
        self.db.add_all([agent1, agent2])

        net.add(agent1)
        net.add(agent2)
        self.db.commit()

        agent1.connect(whom=agent2)
        self.db.commit()

        assert len(net.vectors()) == 1
        assert net.vectors()[0].origin == agent1
        assert net.vectors()[0].destination == agent2

    def test_network_degrees(self):
        net = networks.Network()
        self.db.add(net)
        self.db.commit()

        agent1 = nodes.Agent(network=net)
        agent2 = nodes.Agent(network=net)

        assert [len(n.vectors(direction="outgoing")) for n in net.nodes()] == [0, 0]

        agent1.connect(whom=agent2)

        assert 1 in [len(n.vectors(direction="outgoing")) for n in net.nodes()]
        assert 0 in [len(n.vectors(direction="outgoing")) for n in net.nodes()]

    def test_network_add_source_global(self):
        net = networks.Network()

        agent1 = nodes.Agent()
        agent2 = nodes.Agent()

        # Add agents to network.
        net.add(agent1)
        net.add(agent2)

        self.db.add_all([agent1, agent2])
        self.db.commit()

        source = nodes.RandomBinaryStringSource()
        self.db.add(source)
        net.add(source)
        source.connect(whom=net.nodes(type=nodes.Agent))

        assert len(net.vectors()) == 2
        assert source.network == net
        assert agent1.network == net
        assert [len(n.vectors(direction="outgoing")) for n in net.nodes(type=nodes.Agent)] == [0, 0]
        assert len(net.nodes(type=nodes.Source)[0].vectors(direction="outgoing")) == 2

    def test_network_add_source_local(self):
        net = networks.Network()

        agent1 = nodes.Agent()
        agent2 = nodes.Agent()

        # Add agents to network.
        net.add(agent1)
        net.add(agent2)

        self.db.add_all([agent1, agent2])
        self.db.commit()

        source = nodes.RandomBinaryStringSource()
        self.db.add(source)
        net.add(source)
        source.connect(whom=net.nodes(type=nodes.Agent)[0])

        assert len(net.vectors()) == 1
        assert [len(n.vectors(direction="outgoing")) for n in net.nodes(type=nodes.Agent)] == [0, 0]
        assert len(net.nodes(type=nodes.Source)[0].vectors(direction="outgoing")) == 1

    def test_network_add_agent(self):
        net = networks.Network()

        agent1 = nodes.Agent()
        agent2 = nodes.Agent()
        agent3 = nodes.Agent()
        self.db.add_all([agent1, agent2, agent3])
        self.db.commit()

        net.add(agent1)
        net.add(agent2)
        net.add(agent3)

        self.db.commit()

        assert len(net.nodes(type=nodes.Agent)) == 3
        assert len(net.vectors()) == 0
        assert len(net.nodes(type=nodes.Source)) == 0

    def test_network_downstream_nodes(self):
        net = networks.Network()
        self.db.add(net)
        self.db.commit()

        node1 = models.Node(network=net)
        node2 = models.Node(network=net)
        agent1 = nodes.Agent(network=net)
        agent2 = nodes.ReplicatorAgent(network=net)
        source1 = nodes.Source(network=net)
        source2 = nodes.Source(network=net)

        node1.connect(whom=[node2, agent1, agent2])

        assert_raises(TypeError, node1.connect, whom=source1)

        assert node1.neighbors(connection="to") == [node2, agent1, agent2]
        assert len(node1.vectors(direction="outgoing")) == 3
        assert node1.neighbors(connection="to", type=nodes.Agent) == [agent1, agent2]

        agent1.fail()
        agent2.fail()

        # these assertions removed pending resolution of issue #164
        #assert node1.neighbors(connection="to", status="dead") == [agent1]
        #assert node1.neighbors(connection="to, status="failed") == [agent2]
        #assert node1.neighbors(connection="to, status="alive") == [node2]
        #assert node1.neighbors(connection="to, status="all") == [node2, agent1, agent2]

        assert_raises(ValueError, node1.neighbors, connection="to", failed="blagjrg")

    def test_network_repr(self):
        net = networks.Network()

        agent1 = nodes.Agent()
        agent2 = nodes.Agent()
        self.db.add_all([agent1, agent2])

        net.add(agent1)
        net.add(agent2)

        self.db.commit()

        source = nodes.RandomBinaryStringSource()
        self.db.add(source)

        net.add(source)
        source.connect(whom=net.nodes(type=nodes.Agent))

        assert repr(net) == "<Network-" + str(net.id) + "-base with 3 nodes, 2 vectors, 0 infos, 0 transmissions and 0 transformations>"

    def test_create_chain(self):
        net = networks.Chain()
        self.db.add(net)

        for i in range(4):
            agent = nodes.Agent(network=net)
            net.add_agent(agent)

        source = nodes.RandomBinaryStringSource(network=net)
        net.add_source(source)

        assert len(net.nodes(type=nodes.Agent)) == 4
        assert len(net.nodes(type=nodes.Source)) == 1
        assert len(net.vectors()) == 4
        assert net.nodes(type=nodes.Agent)[0].network == net
        assert net.nodes(type=nodes.Source)[0].network == net

    def test_chain_repr(self):
        net = networks.Chain()
        self.db.add(net)

        for i in range(4):
            agent = nodes.Agent(network=net)
            net.add_agent(agent)

        source = nodes.RandomBinaryStringSource(network=net)
        net.add_source(source)

        assert repr(net) == "<Network-" + str(net.id) + "-chain with 5 nodes, 4 vectors, 0 infos, 0 transmissions and 0 transformations>"

    def test_create_fully_connected(self):
        net = networks.FullyConnected()
        for i in range(4):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)

        assert len(net.nodes(type=nodes.Agent)) == 4
        assert len(net.vectors()) == 12
        assert [len(n.vectors(direction="outgoing")) for n in net.nodes(type=nodes.Agent)] == [3, 3, 3, 3]

    def test_create_empty(self):
        """Empty networks should have nodes, but no edges."""
        net = networks.Empty()
        for i in range(10):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)

        assert len(net.nodes(type=nodes.Agent)) == 10
        assert len(net.vectors()) == 0

    def test_create_empty_with_source(self):
        """A sourced empty network should have nodes and an edge for each."""
        net = networks.Empty()
        for i in range(10):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)

        source = nodes.Source()
        net.add_source(source)

        assert len(net.nodes(type=nodes.Agent)) == 10
        assert len(net.vectors()) == 10

    def test_fully_connected_repr(self):
        net = networks.FullyConnected()
        for i in range(4):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)

        assert repr(net) == "<Network-" + str(net.id) + "-fully-connected with 4 nodes, 12 vectors, 0 infos, 0 transmissions and 0 transformations>"

    def test_create_scale_free(self):
        m0 = 4
        m = 4
        net = networks.ScaleFree(m0=m0, m=m)

        for i in range(m0):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)
        self.db.commit()

        assert len(net.nodes(type=nodes.Agent)) == m0
        assert len(net.vectors()) == m0*(m0 - 1)

        agent1 = nodes.Agent()
        self.db.add(agent1)
        net.add_agent(agent1)
        self.db.commit()
        assert len(net.nodes(type=nodes.Agent)) == m0 + 1
        assert len(net.vectors()) == m0*(m0 - 1) + 2*m

        agent2 = nodes.Agent()
        self.db.add(agent2)
        net.add_agent(agent2)
        self.db.commit()
        assert len(net.nodes(type=nodes.Agent)) == m0 + 2
        assert len(net.vectors()) == m0*(m0 - 1) + 2*2*m

    def test_scale_free_repr(self):
        net = networks.ScaleFree(m0=4, m=4)

        for i in range(6):
            agent = nodes.Agent()
            self.db.add(agent)
            net.add_agent(agent)

        assert repr(net) == "<Network-" + str(net.id) + "-scale-free with 6 nodes, 28 vectors, 0 infos, 0 transmissions and 0 transformations>"

    def test_create_sequential_microsociety(self):
        """Create a sequential microsociety."""
        net = networks.SequentialMicrosociety(n=3, max_size=10)
        self.db.add(net)

        source = nodes.RandomBinaryStringSource(network=net)
        net.add(source)

        agent1 = nodes.Agent(network=net)
        net.add_agent(agent1)

        agent2 = nodes.Agent(network=net)
        net.add_agent(agent2)

        agent3 = nodes.Agent(network=net)
        net.add_agent(agent3)

        agent4 = nodes.Agent(network=net)
        net.add_agent(agent4)

        agent5 = nodes.Agent(network=net)
        net.add_agent(agent5)

        agent6 = nodes.Agent(network=net)
        net.add_agent(agent6)

        assert len(agent1.vectors(direction="outgoing")) == 1
        assert len(agent2.vectors(direction="outgoing")) == 2
        assert len(agent3.vectors(direction="outgoing")) == 2

        assert agent2.is_connected(direction="to", whom=agent3)
        assert agent2.is_connected(direction="to", whom=agent4)
        assert not agent2.is_connected(direction="to", whom=agent5)

        assert agent3.is_connected(direction="to", whom=agent4)
        assert agent3.is_connected(direction="to", whom=agent5)
        assert not agent3.is_connected(direction="to", whom=agent6)

    # def test_discrete_generational(self):
    #     n_gens = 4
    #     gen_size = 4

    #     net = networks.DiscreteGenerational(generations=n_gens, generation_size=gen_size, initial_source=True)

    #     source = nodes.RandomBinaryStringSource()
    #     net.add(source)
    #     self.db.add(source)
    #     agents = []
    #     for i in range(n_gens*gen_size):
    #         agents.append(nodes.Agent())
    #         self.db.add(agents[-1])
    #         net.add(agents[-1])
    #         net.add_agent(agents[-1])

    #     assert len(net.nodes(type=nodes.Source)) == 1
    #     assert len(net.nodes(type=nodes.Agent)) == n_gens*gen_size

    #     for a in range(n_gens*gen_size):
    #         for b in range(n_gens*gen_size):
    #             a_gen = int((a)/float(gen_size))
    #             b_gen = int((b)/float(gen_size))
    #             if b_gen == (1+a_gen):
    #                 assert agents[a].is_connected(direction="to", whom=agents[b])
    #             else:
    #                 assert (agents[a].is_connected(direction="to", whom=agents[b]) is False)
    #             if a_gen == 0:
    #                 assert isinstance(agents[a].neighbors(connection="from")[0], nodes.Source)
