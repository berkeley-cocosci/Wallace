"""Integration tests for Bartlett1932."""

import subprocess
import re
import requests
import threading


class TestBartlett(object):
    """Test class for the demo."""

    def setup(self):
        """Launch the experiment in the sandbox."""
        sandbox_output = subprocess.check_output(
            "cd examples/bartlett1932; wallace sandbox",
            shell=True)

        m = re.search("Running as experiment (.*)...", sandbox_output)
        self.exp_id = m.group(1)
        self.url = "http://" + self.exp_id + ".herokuapp.com"

    def teardown(self):
        """Tear down the app."""
        subprocess.call(
            "heroku apps:destroy --app " + self.exp_id + " --confirm " + self.exp_id,
            shell=True)

    def test_experiment(self):
        """Run the autobots."""
        autobots = 1  # Number of parallel simulated workers.

        # Define the behavior of each worker.
        def autobot(url):
            # create participant
            args = {
                "hitId": "bartlett-test-hit",
                "assignmentId": 1,
                "workerId": 1,
                "mode": "sandbox"
            }
            requests.get(url + "/exp", params=args)

            # send AssignmentAccepted notification
            args = {
                "Event.1.EventType": "AssignmentAccepted",
                "Event.1.AssignmentId": 1
            }
            requests.post(url + "/notifications", data=args)

            # work through the trials
            working = True
            while working is True:

                # Create an agent.
                args = {
                    "unique_id": "1:1"
                }
                agent = requests.post(url + "/agents", data=args)
                working = agent.status_code == 200

                if working:
                    # Get pending transmissions.
                    agent_uuid = agent.json()["agents"]["uuid"]
                    args = {
                        "destination_uuid": agent_uuid
                    }
                    r = requests.get(url + "/transmissions", params=args)
                    assert(r.status_code == 200)

                    # Get info associated with the pending transmission.
                    r = requests.get(url + "/information/" + str(r.json()["transmissions"][0]["info_uuid"]), params=args)
                    assert(r.status_code == 200)

                    # Create a new info.
                    args = {
                        "origin_uuid": agent_uuid,
                        "contents": "test test test",
                        "info_type": "base"
                    }
                    r = requests.post(url + "/information", data=args)
                    assert(r.status_code == 200)

            # Send an AssignmentSubmitted notification.
            args = {
                "Event.1.EventType": "AssignmentSubmitted",
                "Event.1.AssignmentId": 1
            }
            requests.post(url + "/notifications", data=args)
            return

        # Create worker threads.
        threads = []
        for i in range(autobots):
            t = threading.Thread(target=autobot, args=(self.url, ))
            threads.append(t)
            t.start()
