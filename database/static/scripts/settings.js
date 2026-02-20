function delete_time(ttime) {
    location.href = `/settings/delete/time/${ttime}`;
}

function delete_break(btime) {
    location.href = `/settings/delete/break/${btime}`;
}

function new_time() {
    location.href = "/settings/add/time";
}

function new_break() {
    location.href = "/settings/add/break";
}

function timetable_settings() {
    location.href = "/settings/timetable";
}

function user_settings() {
    location.href = "/settings/user";
}

function locations() {
    location.href = "/settings/edit/locations";
}

function new_room() {
    location.href = "/settings/edit/locations/room/new";
}

function delete_room(loc) {
    location.href = `/settings/delete/locations/room/${loc}`;
}

function new_location() {
    location.href = "/settings/edit/locations/location/new";
}

function delete_location(loc) {
    location.href = `/settings/delete/locations/location/${loc}`;
}

function api_settings() {
    location.href = "/settings/api";
}

function regenerate_api_key() {
    location.href = "/settings/api/gen"
}