/*
    Helper functions that are used in multiple places. Not worrying about namespace yet
*/


function get_graph_data(site_id, period_from, period_to) {

    period_from = moment(period_from);
    period_to = moment(period_to);
    parameter_string = site_id + '/' + period_from.format('DD-MM-YYYY') + '/' + period_to.format('DD-MM-YYYY');

    promises = [];
    promises.push(d3.json('/graphs/api/vsw_reading/' + parameter_string + '/?format=json'));
    promises.push(d3.json('/graphs/api/vsw_strategy/' + parameter_string + '/?format=json'));
    promises.push(d3.json('/api/site/' + site_id + '/?format=json'));

    return promises;
    
    /*


    var site_object = {};
    var reading_data = [];
    var rainfall_data = [];
    var irrigation_data = [];
    var critical_data = {};
    var strategy_area_data = [];

    var fullpoint = 0;
    var refill = 0;
    var minReading = undefined;
    var maxReading = undefined;




    Promise.all(promises).then(function(values) {
        values[0].forEach(function(reading) {
            parsed_date = parseTime(reading.date);
            if (reading.type == "Probe") {
                rz1 = Math.round(reading["rz1"]);
                reading_data.push({
                    x : parsed_date,
                    y : rz1
                });
                rainfall_data.push({
                    x : parsed_date,
                    y : reading.rain
                });
                irrigation_data.push({
                    x : parsed_date,
                    y : reading.irrigation_mms
                });
                if (minReading === undefined || rz1 < minReading)
                    minReading = rz1;
                if (maxReading === undefined || rz1 > maxReading)
                    maxReading = rz1;
            } else if (reading.type == "Full Point") {
                fullpoint = Math.round(reading["rz1"]);
            } else if (reading.type == "Refill") {
                refill = Math.round(reading["rz1"]);
            }
        }); // End loop of reading data
        diff = fullpoint - refill;
        values[1].forEach(function(strategy) {
            critical_data[strategy.critical_date_type] = strategy.critical_date;

            var strategyDate = parseTime(strategy.strategy_date);
            var upper = fullpoint - (diff - diff * strategy.percentage);

            strategy_area_data.push({
                x: strategyDate,
                high: upper,
                low: upper - diff * 0.5
            });
        }); // End strategy data loop
        // Sort by date (x) implicitly, dont rely on api call being in date order
        strategy_area_data.sort((a, b) => a.x - b.x);
        reading_data.sort((a, b) => a.x - b.x);
        rainfall_data.sort((a, b) => a.x - b.x);
        irrigation_data.sort((a, b) => a.x - b.x);

        maxY = 0;
        minY = 0;
        if (maxReading >= fullpoint){ maxY = maxReading } else { maxY = fullpoint }
        if (minReading <= refill){ minY = minReading } else { minY = refill }

        site_object = values[2]
        site_object[reading_data]=reading_data
        site_object[rainfall_data]=reading_data
        console.log(site_object)
    });
    */
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
