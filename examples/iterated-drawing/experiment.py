"""Bartlett's trasmission chain experiment from Remembering (1932)."""

from wallace.networks import Chain
from wallace.nodes import Source
from wallace.experiments import Experiment
import random
import json
import os
import base64


class Bartlett1932(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session):
        """Call the same function in the super (see experiments.py in wallace).

        A few properties are then overwritten.
        Finally, setup() is called.
        """
        super(Bartlett1932, self).__init__(session)
        self.experiment_repeats = 1
        self.setup()

    def setup(self):
        """Setup the networks.

        Setup only does stuff if there are no networks, this is so it only
        runs once at the start of the experiment. It first calls the same
        function in the super (see experiments.py in wallace). Then it adds a
        source to each network.
        """
        if not self.networks():
            super(Bartlett1932, self).setup()
            for net in self.networks():
                WarOfTheGhostsSource(network=net)

    def create_network(self):
        """Return a new network."""
        return Chain(max_size=3)

    def add_node_to_network(self, node, network):
        """Add node to the chain and receive transmissions."""
        network.add_node(node)
        parent = node.neighbors(direction="from")[0]
        parent.transmit()
        node.receive()

    def recruit(self):
        """Recruit one participant at a time until all networks are full."""
        if self.networks(full=False):
            self.recruiter().recruit_participants(n=1)
        else:
            self.recruiter().close_recruitment()


class WarOfTheGhostsSource(Source):
    """A Source that reads in a random story from a file and transmits it."""

    __mapper_args__ = {
        "polymorphic_identity": "war_of_the_ghosts_source"
    }

    def _contents(self):
        """Define the contents of new Infos.

        transmit() -> _what() -> create_information() -> _contents().
        """
        img_root = "static/images/characters"
        filenames = os.listdir(img_root)
        random.shuffle(filenames)
        data = []
        for fn in filenames:
            if ".png" in fn:
                # Encode the image in base64.
                encoded = base64.b64encode(
                    open(os.path.join(img_root, fn), "rb").read())

                data.append({
                    "name": fn,
                    "image": "data:image/png;base64," + encoded,
                    "drawing": "",
                    # "strokes": ,
                })

        return json.dumps(data)
