import wallace
from wallace import transformations
from wallace.experiments import Experiment
from wallace.recruiters import SimulatedRecruiter
from wallace.models import Transformation, Info, Agent, Source
from collections import OrderedDict


class SubstitutionCiphersExperiment(Experiment):
    def __init__(self, session):
        super(SubstitutionCiphersExperiment, self).__init__(session)

        self.task = "SubstitutionCipher"
        self.num_agents = 10
        self.num_steps = self.num_agents - 1
        self.network = wallace.networks.FullyConnected(self.session)
        self.process = wallace.processes.RandomWalkFromSource(self.network)
        self.agent_type = SimulatedAgent
        self.recruiter = SimulatedRecruiter

        # Setup for first time experiment is accessed
        if not self.network.nodes(type=Source):
            source = WarOfTheGhostsSource()
            self.network.add(source)
            self.save(source)
            source.connect_to(self.network.nodes(type=Agent))
            self.save()
            print "Added initial source: " + str(source)

        # Open recruitment
        self.recruiter().open_recruitment(exp=self)

    def newcomer_arrival_trigger(self, newcomer):

        self.network.add_agent(newcomer)
        self.save()

        # If this is the first participant, link them to the source.
        if len(self.network.nodes(type=Agent)) == 1:
            source = self.network.nodes(type=Source)[0]
            source.connect_to(newcomer)
            self.save()

        # Run the next step of the process.
        self.process.step()

        newcomer.receive()

        if self.is_experiment_over():
            # If the experiment is over, stop recruiting and export the data.
            self.recruiter().close_recruitment(exp=self)
        else:
            # Otherwise recruit a new participant.
            self.recruiter().recruit_new_participants(exp=self, n=1)

    def is_experiment_over(self):
        return len(self.network.vectors) == self.num_agents

    def apply_substitution_cipher(self, info_in, node, info_out=None):
        transformations.check_for_transformation(info_in=info_in, node=node, info_out=info_out)

        alphabet = "abcdefghijklmnopqrstuvwxyz"
        keyword = "zebras"

        # Generate the ciphertext alphabet
        kw_unique = ''.join(OrderedDict.fromkeys(keyword).keys())
        non_keyword_letters = ''.join([l for l in alphabet if l not in kw_unique])
        ciphertext_alphabet = kw_unique + non_keyword_letters

        text = info_in.contents

        # Do the lower case.
        for i in range(len(alphabet)):
            text = text.replace(alphabet[i], ciphertext_alphabet[i])

        # And the upper case.
        alphabet_up = alphabet.upper()
        ciphertext_alphabet_up = ciphertext_alphabet.upper()
        for i in range(len(alphabet_up)):
            text = text.replace(alphabet_up[i], ciphertext_alphabet_up[i])

        # Create a new info
        info_out = Info(origin=node, contents=text)
        SubstitutionCipher(info_in=info_in, info_out=info_out)

        return info_out


class SimulatedAgent(Agent):
    """A simulated agent that applies a substitution cipher to the text."""

    __mapper_args__ = {"polymorphic_identity": "simulated_agent"}

    def update(self, infos):
        for info in infos:
            # Apply the translation transformation.
            self.transform(type=SubstitutionCipher, info_in=info)


class WarOfTheGhostsSource(Source):
    """A source that transmits the War of Ghosts story from Bartlett (1932).
    """

    __mapper_args__ = {"polymorphic_identity": "war_of_the_ghosts_source"}

    @staticmethod
    def _data(length):
        with open("static/stimuli/ghosts.md", "r") as f:
            return f.read()


class SubstitutionCipher(Transformation):
    """Translates from English to Latin or Latin to English."""

    __mapper_args__ = {"polymorphic_identity": "translation_tranformation"}


if __name__ == "__main__":
    session = wallace.db.init_db(drop_all=False)
    experiment = SubstitutionCiphersExperiment(session)
