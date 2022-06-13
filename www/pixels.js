
// Only one sequence can be selected
var sequence = "";
var reverse = false;

// Used for escaping strings as additional security check
var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

// Should not be required as data comes from our own server
// but provides a little additional protection 
function escapeHtml (string) {
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return entityMap[s];
  });
}


$(() => {

    $('#status').html("<p>Ready</p>");

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
    url_string = "set?seq="+sequence+"&delay="+delay+"&reverse="+reverse_str+"&colors="+color_list;
    $.get( url_string, function (data) {
        // Convert from json to user string
        status_string = format_status (data);
        $("#status").html(status_string);
    });
    
    
}


function format_status(data) {
    obj = JSON.parse(data);
    formatted_string = "";
    if (obj.status =="success") {
        // Displays the short sequence name, which is what would be used
        // in automation etc.
        formatted_string += "LEDs updated "+escapeHtml(obj.sequence);
    }
    else {
        formatted_string += "Update failed "+escapeHtml(obj.msg);
    }
    return formatted_string;    
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
    $("#ulcolchosen").append("<li class=\"licolchosen\"><button name=\""+this_color+"\" class=\"buttoncolchosen chosencolor col"+this_color+"\" style=\"background:#"+this_color+"\" onclick=\"remove_color($(this))\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</button></li>");
}


// Redirect to settings
function settings() {
    window.location.href="settings";
}

// Redirect to login
function login() {
    window.location.href="login";
}

// Redirect to logout
function logout() {
    window.location.href="logout";
}

// Redirect to main page
function go_index() {
    window.location.href="home";
}

// Submit form from button outside of the form
function save_settings() {
    $( "#settingsform" ).submit();
}
