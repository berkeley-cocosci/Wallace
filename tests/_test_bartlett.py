"""Integration tests for Bartlett1932."""

import subprocess
import re
import requests


class TestBartlett(object):

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

    # Simulate participants.
    args = {'hitId': 'bartlett-test-hit', 'assignmentId': 1, 'workerId': 1, 'mode': 'sandbox'}
    participant = requests.get(url + '/exp', params=args)
    #print participant.text

    args = {
        'Event.1.EventType': 'AssignmentAccepted',
        'Event.1.AssignmentId': 1
    }
    notification = requests.post(url + '/notifications', data=args)

    working = True
    while working is True:
        args = {'unique_id': '1:1'}
        agent = requests.post(url + '/agents', data=args)
        working = agent.status_code == 200
        if working is True:
            agent_uuid = agent.json()['agents']['uuid']
            args = {'destination_uuid': agent_uuid}
            transmission = requests.get(url + '/transmissions', data=args)
            info = requests.get(url + '/information/' + str(transmission.json()['transmissions'][0]['info_uuid']), data=args)
            args = {'origin_uuid': agent_uuid, 'contents': 'test test test', 'info_type': 'base'}
            requests.post(url + '/information', data=args)

    #subprocess.call("heroku apps:destroy --app " + exp_id + " --confirm " + exp_id, shell=True)
    # for app in $(heroku apps | sed '/[pt]/ d'); do heroku apps:destroy --app $app --confirm $app; done
