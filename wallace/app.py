from flask import Flask, json, request, Response
import agents
import experiments
import models
import db

app = Flask(__name__)

session = db.init_db(drop_all=True)
experiment = experiments.Demo2(session)


@app.route("/")
def index():
    return "Index page"


@app.route("/agents", methods=["POST", "GET"])
def api_agent_create():

    if request.method == 'POST':

        # Create the newcomer and insert into the network
        newcomer = agents.Agent()
        experiment.network.add_agent(newcomer)

        # Trigger the next step of the process
        experiment.process.step()

        # Return a response
        data = {'agents': {'uuid': newcomer.uuid}}
        js = json.dumps(data)
        resp = Response(js, status=200, mimetype='application/json')
        return resp

    if request.method == "GET":
        data_agents = [agent.uuid for agent in experiment.network.agents]
        data = {"agents": data_agents}
        js = json.dumps(data)
        resp = Response(js, status=200, mimetype='application/json')
        return resp


@app.route("/transmissions", defaults={"transmission_uuid": None}, methods=["POST", "GET"])
@app.route("/transmissions/<transmission_uuid>", methods=["GET"])
def api_transmission(transmission_uuid):

    if request.method == 'GET':

        if transmission_uuid is None:
            requesting_agent = experiment.network.last_node  # FIXME, assumes chain
            pending_transmissions = requesting_agent.pending_transmissions

        else:
            transmission = models.Transmission\
                .query\
                .filter_by(uuid=transmission_uuid)\
                .one()
            pending_transmissions = [transmission]

        data_transmissions = []
        for i in xrange(len(pending_transmissions)):
            t = pending_transmissions[i]
            data_transmissions.append({
                "uuid": t.uuid,
                "meme_uuid": t.meme_uuid,
                "origin_uuid": t.origin_uuid,
                "destination_uuid": t.destination_uuid,
                "transmit_time": t.transmit_time,
                "receive_time": t.receive_time
            })
            data = {"transmissions": data_transmissions}

        js = json.dumps(data)
        resp = Response(js, status=200, mimetype='application/json')
        return resp

    if request.method == "POST":

        meme = models.Meme\
            .query\
            .filter_by(uuid=request.args['meme_uuid'])\
            .one()

        destination = agents.Agent\
            .query\
            .filter_by(uuid=request.args['destination_uuid'])\
            .one()

        transmission = models.Transmission(meme=meme, destination=destination)

        data = {'uuid': transmission.uuid}
        js = json.dumps(data)

        resp = Response(js, status=200, mimetype='application/json')
        return resp


@app.route("/memes/", defaults={"meme_uuid": None}, methods=["POST"])
@app.route("/memes/<meme_uuid>", methods=["GET"])
def api_meme(meme_uuid):

    if request.method == 'GET':

        if meme_uuid is not None:
            meme = models.Meme.query.filter_by(uuid=meme_uuid).one()

            data = {
                'meme_uuid': meme_uuid,
                'contents': meme.contents,
                'origin_uuid': meme.origin_uuid,
                'creation_time': meme.creation_time,
                'type': meme.type
            }
            js = json.dumps(data)

            resp = Response(js, status=200, mimetype='application/json')
            return resp

    if request.method == "POST":

        if 'origin_uuid' in request.args:

            # models
            node = models.Node\
                .query\
                .filter_by(uuid=request.args['origin_uuid'])\
                .one()

            meme = models.Meme(
                origin=node,
                origin_uuid=request.args['origin_uuid'],
                contents=request.args['contents'])

            data = {'uuid': meme.uuid}
            js = json.dumps(data)

            resp = Response(js, status=200, mimetype='application/json')
            return resp


if __name__ == "__main__":
    app.debug = True
    app.run()
