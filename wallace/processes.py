"""Processes manipulate networks and their parts."""

from wallace.models import *
from wallace.nodes import *


def random_walk(network):
    """Take a random walk from a source.

    Start at a node randomly selected from those that receive input from a
    source. At each step, transmit to a randomly-selected downstream node.
    """
    # work out who is going to transmit
    if ((not network.transmissions()) or (network.latest_transmission_recipient() is None)):
        sender = random.choice(network.nodes(type=Source))
    else:
        sender = network.latest_transmission_recipient()

    receiver = random.choice(sender.neighbors(connection="to", type=Agent))

    sender.transmit(to_whom=receiver)


def moran_cultural(network):
    """The generalized cultural Moran process plays out over a network. At each
    time step, an individual is chosen to receive information from another
    individual. Nobody dies, but perhaps their ideas do."""

    if not network.transmissions():  # first step, replacer is a source
        replacer = random.choice(network.nodes(type=Source))
        replacer.transmit()
    else:
        replacer = random.choice(network.nodes(type=Agent))
        replaced = random.choice(replacer.neighbors(connection="to", type=Agent))
        replacer.transmit(what=replacer.infos()[-1], to_whom=replaced)


def moran_sexual(network):
    """The generalized sexual Moran process also plays out over a network. At
    each time step, and individual is chosen for replication and another
    individual is chosen to die. The replication replaces the one who dies.

    For this process to work you need to add a new agent before calling step.
    """

    if not network.transmissions():
        replacer = random.choice(network.nodes(type=Source))
        replacer.transmit()
    else:
        replacer = random.choice(network.nodes(type=Agent)[:-1])
        replaced = random.choice(replacer.neighbors(connection="to", type=Agent))

        # Find the baby just added
        baby = network.nodes(type=Agent)[-1]

        # Give the baby the same outgoing connections as the replaced.
        for node in replaced.neighbors(connection="to"):
            baby.connect_to(node)

        # Give the baby the same incoming connections as the replaced.
        for node in replaced.neighbors(connection="from"):
            node.connect_to(baby)

        # Kill the replaced agent.
        replaced.die()

        # Endow the baby with the ome of the replacer.
        replacer.transmit(to_whom=baby)


def transmit_by_fitness(to_whom=None, what=None, from_whom=Agent):

    parents = to_whom.neighbors(connection="from", type=from_whom)
    parent_fitnesses = [p.fitness() for p in parents]
    parent_probs = [(f/(1.0*sum(parent_fitnesses))) for f in parent_fitnesses]

    rnd = random.random()
    temp = 0.0
    for i, probability in enumerate(parent_probs):
        temp += probability
        if temp > rnd:
            parent = parents[i]
            break

    parent.transmit(what=what, to_whom=to_whom)
