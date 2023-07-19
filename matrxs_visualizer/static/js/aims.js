$(document).ready(function() {

    // only show the communication of the agent we are viewing right now
    if (lv_agent_id == "explorer") {
        document.getElementById("rescue_worker_communication").style.display = "none";
    } else if(lv_agent_id == "rescue_worker") {
        document.getElementById("explorer_communication").style.display = "none";
    }


    /**************************************************************
    * Rescue worker communication fields
    ***************************************************************/

    // Question: determine building status of building X
    document.getElementById("rw_building_status").addEventListener("click", function() {
        var id = "rw_building_status";
        console.log("rw building status click")
        var select = document.getElementById(id + "_select");
        var selected = select.options[select.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected.value != "placeholder") {
            send_aims_message(id, "Bepaal de status van gebouw " + selected.text)
        }
    });

    // Question: Open door of building X
    document.getElementById("rw_open_door").addEventListener("click", function() {
        var id = "rw_open_door";
        console.log("rw open door click")
        var select = document.getElementById(id + "_select");
        var selected = select.options[select.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected.value != "placeholder") {
            send_aims_message(id, "Verwijder het puin voor de ingang van gebouw " + selected.text)
        }
    });

    // Question: report battery status
    document.getElementById("rw_battery_status").addEventListener("click", function() {
        send_aims_message("", "Rapporteer de status van je batterij.", false)
    });

    // Question: stop current task
    document.getElementById("rw_stop_task").addEventListener("click", function() {
        send_aims_message("", "Stop met je huidige taak.", false)
    });

    // Question: Continue previous task
    document.getElementById("rw_continue_task").addEventListener("click", function() {
        send_aims_message("", "Ga verder met je vorige taak.", false)
    });

    // Question: Locate victims in building X
    document.getElementById("rw_locate_victims").addEventListener("click", function() {
        var id = "rw_locate_victims";
        console.log("rw open door click")
        var select = document.getElementById(id + "_select");
        var selected = select.options[select.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected.value != "placeholder") {
            send_aims_message(id, "Lokaliseer en meld slachtoffers in gebouw " + selected.text)
        }
    });

    // Question: Take victim V[n] in building B[n] to commando post
    document.getElementById("rw_victim_to_cp").addEventListener("click", function() {
        var id = "rw_victim_to_cp";
        console.log("rw victim to cp")
        var select = document.getElementById(id + "_select1");
        var selected = select.options[select.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected.value != "placeholder") {
            send_aims_message(id, "Breng slachtoffer " + selected.text + " naar de commandopost.", false);
            reset_select(id + "_select1");
        }
    });

    // Question: Take victim V[n] in building B[n] to outside of building
    document.getElementById("rw_victim_outside").addEventListener("click", function() {
        var id = "rw_victim_outside";
        console.log("rw victim to outside building")
        var select = document.getElementById(id + "_select1");
        var selected = select.options[select.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected.value != "placeholder") {
            send_aims_message(id, "Verplaats slachtoffer " + selected.text + " buiten het gebouw.", false);
            reset_select(id + "_select1");
        }
    });

    /**************************************************************
    * Explorer communication fields
    ***************************************************************/

    // Answer: report battery status
    document.getElementById("expl_battery_status").addEventListener("click", function() {
        send_userinput_to_MATRXS('1');
    });

    // Answer: Building B[n] has status collapsed: [no/yes]
    document.getElementById("expl_building_status").addEventListener("click", function() {
        var id = "expl_building_status";
        console.log("expl building has status")
        var select = document.getElementById(id + "_select1");
        var selected1 = select.options[select.selectedIndex];

        var select2 = document.getElementById(id + "_select2");
        var selected2 = select2.options[select2.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected1.value != "placeholder" && selected2.value != "placeholder") {
            send_aims_message(id, "Gebouw " + selected1.text + " heeft status ingestort: " + selected2.text, false);
            reset_select(id + "_select1");
            reset_select(id + "_select2");
        }
    });

    // Answer: In building B[n] there is/are [n] victim(s)
    document.getElementById("expl_n_victims").addEventListener("click", function() {
        var id = "expl_n_victims";
        console.log("expl # victims in building")
        var select = document.getElementById(id + "_select1");
        var selected1 = select.options[select.selectedIndex];

        var select2 = document.getElementById(id + "_select2");
        var selected2 = select2.options[select2.selectedIndex];

        // send a message if the user selected something else than the placeholder
        if (selected1.value != "placeholder" && selected2.value != "placeholder") {
            send_aims_message(id, "In gebouw " + selected1.text + " zijn er " + selected2.text + " slachtoffers", false);
            reset_select(id + "_select1");
            reset_select(id + "_select2");
        }
    });

});


/**
 * Sends the message to MATRX, and resets the select
 */
function send_aims_message(id, content, reset=true) {
    console.log("Aims trying to send message:", content)
    data = {"content": content, "sender": lv_agent_id, "receiver": null} // receiver null = globally addressed
    send_matrx_api_post_message("send_message", data);

    if (reset) {
        reset_select(id + "_select"); // reset select
    }
}

/*
 * Reset the selected value in a dropdown, and select the placeholder
 */
function reset_select(id){
    var elements = document.getElementById(id).options;

    for(var i = 0; i < elements.length; i++){
        elements[i].selected = false;
        if (i == 0) {
            elements[i].selected = true;
        }
    }
}


