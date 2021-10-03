
// Only one sequence can be selected
var sequence = "";
var reverse = false;

$(() => {

    $('#status').html("<p>Status updated!</p>");

    $.getJSON( "sequences.json", {
        tagmode: "any",
        format: "json"
    }) 
    .done(function( data ) {
        seq_name = "";
        title = "";
        description = "";
        $.each( data, function( i, seq_object ) {
            $.each (seq_object, function (key, val) {
                if (key == "seq_name") seq_name = val;
                if (key == "title") title = val;
                if (key == "description") description = val;
                if (key == "group") group = parseInt(val);
            });
            // Only show groups up to 3
            if (group < 4) {
                // Add to list
                $('#sequences-list').append ("<li class=\"li-seq-select\">\n<button type=\"button\" id=\""+seq_name+"\"  title=\""+description+"\" class=\"seq-select-btn\" onclick=\"select_sequence('"+seq_name+"')\">"+title+"</button>\n</li>");
                // if this is the first then set it to the sequence
                if (sequence == "") sequence = seq_name;
            }
        });
        // Set sequence 
        set_sequence();
        
        
        $(".colbutton").click(function() {
            add_color($(this).attr('name'));
        });
        

    
    });
    

})

// Set all sequences not selected, except one matching sequence
function set_sequence() {
    $.each($(".seq-select-btn"), function (i, val) {
        if (val.id != sequence) {
          $(this).removeClass('sequence-selected');
        }
        else {
          $(this).addClass('sequence-selected');
        }
    }); 
}

function select_sequence(seq_name) {
    sequence = seq_name;
    set_sequence();
}

function reverse_toggle() {
    if (reverse == true) {
        reverse = false;
        $("#reversebutton").removeClass('reverse-selected');
        $("#reversebutton").addClass('reverse-not-selected');
    }
    else {
        reverse = true;
        $("#reversebutton").removeClass('reverse-not-selected');
        $("#reversebutton").addClass('reverse-selected');
    }
}

function apply() {
    // Read each of the values and create the url
    // sequence is in variable sequence
    // get speed
    delay = 1000 - document.getElementById("speed").value;
    // reverse 
    reverse_str = 0;
    if (reverse == true) {
        reverse_str = 1;
    }
    // get all colors
    var color_list = "";
    $.each($(".chosencolor"), function (i, val) {
        // if first don't need comma
        if (color_list != "") color_list += ",";
        color_list += val.name;
    });
    // if no colors send default = white
    if (color_list == "") color_list = "ffffff";
    url_string = "/set?seq="+sequence+"&delay="+delay+"&reverse="+reverse_str+"&colors="+color_list;
    $.get( url_string, function (data) {
        $("#status").html(data);
    });
    
    
}

function show_speed() {
    // JQuery does not work well with manual slider
    // Use normal javascript to get the value
    speed_val = document.getElementById("speed").value;
    document.getElementById("speed-val").innerHTML = 1000-speed_val;
    
}


function remove_color(this_button) {
    this_button.closest('li').remove();
    // check if this was the list button - in which case show default
    if (!($(".chosencolor")[0])) {
        $("#defaultcolchosen").show();
    }
}


function add_color(this_color) {
    // hide the default if not already hidden
    $("#defaultcolchosen").hide();
    // Add this list element
    // chosencolor class is not for css, but for iterating over the 
    // chosen colors (excluding default)
    $("#ulcolchosen").append("<li class=\"licolchosen\"><button name=\""+this_color+"\" class=\"buttoncolchosen chosencolor\" style=\"background:#"+this_color+"\" onclick=\"remove_color($(this))\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</button></li>");
}



