"""Integration tests for Bartlett1932."""

import subprocess
import re
import requests
import threading


class TestBartlett(object):

    # How many parallel simulated workers do you want
    autobots = 1

    # Launch the experiment in the sandbox.
    sandbox_output = subprocess.check_output(
        "cd examples/bartlett1932; wallace sandbox",
        shell=True)

    m = re.search('Running as experiment (.*)...', sandbox_output)
    exp_id = m.group(1)
    url = "http://" + exp_id + ".herokuapp.com"

    # Open the logs in the browser.
    subprocess.call(
        "cd examples/bartlett1932; wallace logs --app " + exp_id,
        shell=True)

    # methods that defines the behavior of each worker
    def autobot(url):
        # create participant
        args = {'hitId': 'bartlett-test-hit', 'assignmentId': 1, 'workerId': 1, 'mode': 'sandbox'}
        requests.get(url + '/exp', params=args)

        # send AssignmentAccepted notification
        args = {
            'Event.1.EventType': 'AssignmentAccepted',
            'Event.1.AssignmentId': 1
        }
        requests.post(url + '/notifications', data=args)

        # work through the trials
        working = True
        while working is True:
            args = {'unique_id': '1:1'}
            agent = requests.post(url + '/agents', data=args)
            working = agent.status_code == 200
            if working is True:
                agent_uuid = agent.json()['agents']['uuid']
                args = {'destination_uuid': agent_uuid}
                transmission = requests.get(url + '/transmissions', params=args)
                requests.get(url + '/information/' + str(transmission.json()['transmissions'][0]['info_uuid']), params=args)
                args = {'origin_uuid': agent_uuid, 'contents': 'test test test', 'info_type': 'base'}
                requests.post(url + '/information', data=args)

        # send AssignmentSubmitted notification
        args = {
            'Event.1.EventType': 'AssignmentSubmitted',
            'Event.1.AssignmentId': 1
        }
        requests.post(url + '/notifications', data=args)
        return

    # create worker threads
    threads = []
    for i in range(autobots):
        t = threading.Thread(target=autobot, args=(url, ))
        threads.append(t)
        t.start()

    #subprocess.call("heroku apps:destroy --app " + exp_id + " --confirm " + exp_id, shell=True)
    # for app in $(heroku apps | sed '/[pt]/ d'); do heroku apps:destroy --app $app --confirm $app; done
