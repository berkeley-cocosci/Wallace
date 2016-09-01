var canvases = [];

// Create the agent.
create_agent = function() {
    reqwest({
        url: "/node/" + participant_id,
        method: 'post',
        type: 'json',
        success: function (resp) {
            my_node_id = resp.node.id;
            get_info(my_node_id);
        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            if (err_response.hasOwnProperty('html')) {
                $('body').html(err_response.html);
            } else {
                allow_exit();
                go_to_page('questionnaire');
            }
        }
    });
};

get_info = function() {
    reqwest({
        url: "/node/" + my_node_id + "/received_infos",
        method: 'get',
        type: 'json',
        success: function (resp) {
            story = JSON.parse(resp.info.contents);
            setTimeout(function () {
                for (var i = 0; i < story.length; i++) {
                    img = new Image();
                    img.src = story[i].image;
                    cvs = canvasobj("stimulus-" + i, img);
                    $("#drawing").append(cvs.getDOMelem());
                    $("#stimulus-" + i + "_canvas").attr("width", "100px");
                    $("#stimulus-" + i + "_canvas").attr("height", "100px");
                    canvases.push(cvs);
                }
            }, 100);
            $("#submit-response").removeClass('disabled');
            $("#submit-response").html('Submit');
        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            $('body').html(err_response.html);
        }
    });
};

submit_response = function() {
    $("#submit-response").addClass('disabled');
    $("#submit-response").html('Sending...');

    response = [];
    for (var i = 0; i < story.length; i++) {
        response.push({
            "name": story[i],
            "image": canvases[i].getImage(),
            "drawing": cvs.getDrawing(),
        });
    }

    reqwest({
        url: "/info/" + my_node_id,
        method: 'post',
        data: {
            contents: JSON.stringify(response),
            info_type: "Info"
        },
        success: function (resp) {
            create_agent();
        }
    });
};
