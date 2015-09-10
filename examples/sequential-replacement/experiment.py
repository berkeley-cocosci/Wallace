"""A function-learning experiment."""

from wallace.experiments import Experiment
from wallace.nodes import ReplicatorAgent, Source
from wallace.networks import SequentialMicrosociety
from wallace import processes
import random
import json
from sqlalchemy.ext.declarative import declared_attr
import math


class SequentialReplacement(Experiment):

    """Defines the experiment."""

    def __init__(self, session):
        """Set up the initial networks."""
        super(SequentialReplacement, self).__init__(session)

        self.practice_repeats = 0
        self.experiment_repeats = 1
        self.agent = ReplicatorAgent
        self.network = lambda: SequentialMicrosociety(n=3, max_size=10)

        self.setup()

    def setup(self):
        """Setup for first time experiment is accessed."""
        if not self.networks():
            super(SequentialReplacement, self).setup()
            for net in self.networks():
                if not net.nodes(type=Source):
                    source = SinusoidalFunctionSource(network=net)
                    net.add(source)
            self.save()

    def create_agent_trigger(self, agent, network):
        """When an agent is created, add it to the network and take a step."""
        network.add_agent(agent)

        # Connect up the source up to all the noninitial members, too.
        source = network.nodes(type=Source)[0]
        if not source.is_connected(direction="to", whom=agent):
            source.connect(direction="to", whom=agent)

        # Transmit to the newcomer.
        for neighbor in agent.neighbors(connection="from"):
            neighbor.transmit(to_whom=agent)


class AbstractFnSource(Source):

    """Abstract class for sources that send functions."""

    __abstract__ = True

    def _contents(self):
        x_min = 1
        x_max = 100

        x_values = random.sample(xrange(x_min, x_max), 20)
        y_values = [self.func(x) for x in x_values]

        data = {"x": x_values, "y": y_values}

        return json.dumps(data)

    @declared_attr
    def __mapper_args__(cls):
        """The name of the source is derived from its class name."""
        return {"polymorphic_identity": cls.__name__.lower()}


class IdentityFunctionSource(AbstractFnSource, Source):

    """A source that transmits the identity function."""

    def func(self, x):
        """f(x) = x."""
        return x


class AdditiveInverseFunctionSource(AbstractFnSource, Source):

    """A source that transmits the identity function."""

    def func(self, x):
        return 100 - x


class SinusoidalFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 50.5 + 49.5 * math.sin(math.pi / 2 + x / (5 * math.pi))


class RandomMappingFunctionSource(AbstractFnSource, Source):
    m = random.shuffle(range(1, 100))

    def func(self, x):
        return self.m[x - 1]


class StepFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 75 if x >= 50 else 25


class ConstantFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 50


class LogisticFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 1 / (0.01 + math.exp(-0.092 * x))


class ExponentialFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 100 * math.exp(-0.05 * x)


class TriangleWaveFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 2 * (100 - x) if x >= 50 else 2 * x


class SquareWaveFunctionSource(AbstractFnSource, Source):
    def func(self, x):
        return 75 if (math.fmod(x, 50) <= 25) else 25
