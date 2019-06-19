var states = ["Finished", "Transferring", "Negotiating", "Waiting", "Establishing",
              "Initiating", "Connecting", "Queued", "Address", "Status", "Offline",
              "Closed", "Can't Connect", "Aborted", "Not Shared"];

var create_table = function() {
    return $('<table />');
};

var add_table_row = function(table, colvals, is_header) {
    var row = $('<tr />');
    var elem;
    if (is_header) { elem = '<th />'; }
    else { elem = '<td />'; }
    for (var ii = 0; ii < colvals.length; ii++) {
        $(elem).html(colvals[ii]).appendTo(row);
    }
    row.appendTo(table);
};

var create_click_link = function(text, func) {
    return $('<a />').click(func).text(text).attr('href', 'javascript:void(0);');
};

var create_hover_link = function(text, over, out) {
    var d = $('<div />').addClass('hover_link').mouseover(over).mouseout(out);
    $('<a />').text(text).attr('href', 'javascript:void(0);').appendTo(d);
    return d;
};

var wrap_text_in_div = function(t) {
    return $('<div />').text(t);
};

var download_file = function(ticket, user, index) {
    var d = new FormData();
    d.append('ticket', ticket);
    d.append('user', user);
    d.append('index', index);
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {}
    r.open('POST', '/download', true);
    r.send(d);
};

var abort_download = function(hash, do_delete) {
    var d = new FormData();
    d.append('hash', hash);
    if (do_delete) d.append('rmfile', 'true');
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {}
    r.open('DELETE', '/download', true);
    r.send(d);
};

var abort_upload = function(hash, do_delete) {
    var d = new FormData();
    d.append('hash', hash);
    if (do_delete) d.append('rmfile', 'true');
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {}
    r.open('DELETE', '/upload', true);
    r.send(d);
};

var get_user_info = function(user, func) {
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) func($.parseJSON(this.responseText));
    };
    r.open('GET', "/user?user=" + user, true);
    r.send();
};

var get_search_results = function(ticket) {
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var j = $.parseJSON(this.responseText),
                table = create_table(),
                cols = ['USER', 'PATH', 'SIZE', 'TYPE', 'RATE', 'LENGTH'].map(wrap_text_in_div);
            add_table_row(table, cols, 1);
            for (var user in j) {
                for (var ii = 0; ii < j[user].length; ii++) {
                    var sr = j[user][ii];

                    cols = [user, sr[0], sr[1], sr[2], sr[3][0], sr[3][1]].map(wrap_text_in_div);
                    cols[0] = create_hover_link(user, function(e) {
                        get_user_info($(this).data('user'), function(j) {
                            var t = 'user: ' + j['user'] + ', image: ' + j['image'] + ', info: ' + j['info'] +
                                ', uploads: ' + j['uploads'] + ', queue: ' + j['queue'] + ', free: ' + j['free'] +
                                ', speed: ' + j['speed'];
                            $('#user_hover_box').text(t);
                            var h = $('#user_hover_box').height();
                            /* NOTE: Need to offset tooltip a bit otherwise when it shows up it can cover the element
                            that triggered MouseOver event, which, in turn, will cause MouseOut event, and so on...
                            Causing tooltip to flicker. */
                            $('#user_hover_box').css({left: e.pageX + 3, top: (e.pageY - h - 3)}).show();
                        });
                    }, function(e) {
                        $('#user_hover_box').hide();
                    }).data('user', user);

                    cols[1] = create_click_link(sr[0], function() {
                        var t = $(this).data('ticket'),
                            u = $(this).data('user'),
                            i = $(this).data('index');
                        download_file(t, u, i);
                    }).data('index', ii).data('ticket', ticket).data('user', user);

                    add_table_row(table, cols, 0);
                }
            }
            $('#search_results').html(table);
        }
    }
    r.open('GET', "/search?ticket=" + ticket, true);
    r.send();
};

// READY

$(document).ready(function() {
    // get downloads button
    $('#btn_downloads').click(function() {
        var r = new XMLHttpRequest();
        r.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var j = $.parseJSON(this.responseText),
                    table = create_table(),
                    cols = ['USER', 'PATH', 'POSITION', 'RATE', 'SIZE', 'STATE', 'A', 'D'].map(wrap_text_in_div);
                add_table_row(table, cols, 1);
                for (var dk in j) {
                    var d = j[dk];
                    cols = [d['user'], d['path'], d['pos'], d['rate'], d['size'], states[parseInt(d['state'])], '#', '#'].map(wrap_text_in_div);
                    cols[6] = create_click_link('#', function() { abort_download($(this).data('hash'), false); }).data('hash', dk);
                    cols[7] = create_click_link('#', function() { abort_download($(this).data('hash'), true); }).data('hash', dk);
                    add_table_row(table, cols, 0);
                }
                $('#downloads').html(table);
            }
        }
        r.open('GET', '/downloads', true);
        r.send();
    });

    // get uploads button
    $('#btn_uploads').click(function() {
        var r = new XMLHttpRequest();
        r.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var j = $.parseJSON(this.responseText),
                    table = create_table(),
                    cols = ['USER', 'PATH', 'POSITION', 'RATE', 'SIZE', 'STATE', 'A', 'D'].map(wrap_text_in_div);
                add_table_row(table, cols, 1);
                for (var dk in j) {
                    var d = j[dk];
                    cols = [d['user'], d['path'], d['pos'], d['rate'], d['size'], states[parseInt(d['state'])], '#', '#'].map(wrap_text_in_div);
                    cols[6] = create_click_link('#', function() { abort_upload($(this).data('hash'), false); }).data('hash', dk);
                    cols[7] = create_click_link('#', function() { abort_upload($(this).data('hash'), true); }).data('hash', dk);
                    add_table_row(table, cols, 0);
                }
                $('#uploads').html(table);
            }
        }
        r.open('GET', '/uploads', true);
        r.send();
    });

    $('#btn_search').click(function() {
        var d = new FormData();
        d.append('query', $('#txt_search').val());
        var r = new XMLHttpRequest();
        r.onreadystatechange = function() {}
        r.open('POST', '/search', true);
        r.send(d);
    });

    $('#btn_get_search').click(function() {
        get_search_results($('#txt_search_ticket_get').val());
    });

    $('#btn_searches').click(function() {
        var r = new XMLHttpRequest();
        r.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var j = $.parseJSON(this.responseText),
                    span = $('<span />');
                for (var ii = 0; ii < j.length; ii++) {
                    if (ii > 0) {
                        span.append(document.createTextNode(', '));
                    }
                    create_click_link(j[ii], function() {
                        var t = $(this).text();
                        get_search_results(t);
                        $('#txt_search_ticket_get').val(t);
                    }).appendTo(span);
                }
                $('#searches').html(span);
            }
        }
        r.open('GET', '/searches', true);
        r.send();
    });

    $('#btn_users').click(function() {
        var r = new XMLHttpRequest();
        r.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var j = $.parseJSON(this.responseText),
                    table = create_table(),
                    cols = ['USER', 'FREE SLOTS', 'QUEUE', 'SPEED', 'INFO', 'IMG', 'UPLOADS'].map(wrap_text_in_div);
                add_table_row(table, cols, 1);
                for (var user in j) {
                    var u = j[user];
                    cols = [user, u['free'], u['queue'], u['speed'], u['info'], u['image'], u['uploads']].map(wrap_text_in_div);
                    add_table_row(table, cols, 0);
                }
                $('#users').html(table);
            }
        }
        r.open('GET', '/users', true);
        r.send();
    });
});
