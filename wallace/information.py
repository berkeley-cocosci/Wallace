"""Subclasses of information."""

from wallace.models import *


class Gene(Info):
    __mapper_args__ = {"polymorphic_identity": "gene"}


class Meme(Info):
    __mapper_args__ = {"polymorphic_identity": "meme"}


class State(Info):
    __mapper_args__ = {"polymorphic_identity": "state"}
