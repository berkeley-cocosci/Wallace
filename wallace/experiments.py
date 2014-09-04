import processes
import agents
import networks
import db


class Experiment(object):
    def __init__(self, session):
        self.task = "Experiment title"
        self.session = session

    def add_sources(self):
        pass

    def step(self):
        pass


class Demo2(Experiment):
    def __init__(self, session):
        super(Demo2, self).__init__(session)
        self.task = "Demo2"
        self.num_agents = 10
        self.num_steps = 9
        self.network = networks.Chain(self.session, self.num_agents)
        self.process = processes.RandomWalkFromSource(self.network)

        # Set up the chain by creating a source
        source = agents.RandomBinaryStringSource()
        self.network.add_node(source)
