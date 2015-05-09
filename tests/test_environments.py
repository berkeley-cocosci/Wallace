from wallace import db
from wallace.models import *
from wallace.nodes import *
from wallace.information import *


class TestEnvironments(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def add(self, *args):
        self.db.add_all(args)
        self.db.commit()

    def test_create_environment(self):
        """Create an environment"""
        environment = Environment()
        state = State(origin=environment, contents="foo")
        self.add(environment, state)

        assert len(environment.uuid) == 32
        assert environment.type == "environment"
        assert environment.creation_time
        assert environment.state().contents == "foo"

    def test_create_environment_get_observed(self):
        environment = Environment()
        state = State(origin=environment, contents="foo")
        self.add(environment, state)

        agent = ReplicatorAgent()
        self.add(agent)

        environment.connect_to(agent)
        environment.transmit(to_whom=agent)
        agent.receive()

        assert agent.infos()[0].contents == "foo"
