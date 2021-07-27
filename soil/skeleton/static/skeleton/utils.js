/*
    Helper functions that are used in multiple places. Not worrying about namespace yet
*/


function get_graph_data(site_id, period_from, period_to, season_id) {

    period_from = moment(period_from);
    period_to = moment(period_to);
    parameter_string = site_id + '/' + period_from.format('DD-MM-YYYY') + '/' + period_to.format('DD-MM-YYYY');

    promises = [];
    promises.push(d3.json('/graphs/api/vsw_reading/' + parameter_string + '/?format=json'));
    promises.push(d3.json('/graphs/api/vsw_strategy/' + parameter_string + '/?format=json'));
    promises.push(d3.json('/api/site/' + site_id + '/?format=json'));
    if (season_id) {
        promises.push(d3.json("/graphs/api/v3/fruition_summary/" + season_id + "/False/sites_summary/?sites[]=" + site_id));
    }
    return promises;


}

function updateMessages(messages){
    $("#div_messages").empty();
    $.each(messages, function (i, m) {
                    $("#div_messages").append("<div class='alert " + m.extra_tags + " alert-dismissible' role='alert'>" +
                    "<button type='button' class='close' data-dismiss='alert' aria-label='Close'>" +
                    "<span aria-hidden='true'>&times;</span>" +
                    "</button>" +
                    m.message + "</div>");
    });
}

/*
    Called to populate Reading Recommendation box as well as calculate and reorganise day hours
*/
function updateReadingRecommendations(week_start_abbr, week_start) {
    function reorder(data, index) {
        return data.slice(index).concat(data.slice(0, index));
    }

    first_day = document.getElementById("week-days").firstElementChild.getAttribute("id");

    if (first_day != week_start_abbr) {
        wrapper = $('#week-days');

        var days_input = wrapper.children();

        arr = [0,1,2,3,4,5,6];
        arr = reorder(arr, week_start)
        wrapper.append( $.map(arr, function(v){ return days_input[v] }) );

        wrapper = $('#week-day-labels');
        var days_label = wrapper.children();
        wrapper.append( $.map(arr, function(v){ return days_label[v] }) );

        wrapper = $('#week-days-water');
        var days_water = wrapper.children();
        wrapper.append( $.map(arr, function(v){ return days_water[v] }) );
    }
}
