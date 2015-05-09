from wallace import db, models, transformations
import random


class TestTransformations(object):

    def setup(self):
        self.db = db.init_db(drop_all=True)

    def teardown(self):
        self.db.rollback()
        self.db.close()

    def add(self, *args):
        self.db.add_all(args)
        self.db.commit()

    def test_replication(self):
        node = models.Node()
        self.db.add(node)
        self.db.commit()

        info_in = models.Info(origin=node, contents="foo")

        info_out = transformations.replicate(node=node, info_in=info_in, info_out=None)

        info_out = node.infos()[-1]

        assert info_out.contents == "foo"

    def test_shuffle_transformation(self):
        node = models.Node()
        self.db.add(node)
        self.db.commit()

        info_in = models.Info(origin=node, contents="foo")
        self.db.add(info_in)
        self.db.commit()

        info_out = transformations.shuffle(info_in=info_in, node=node)

        assert info_out.contents in ["foo", "ofo", "oof"]
