function home() {
    location.href = "/";
}

function edit(day) {
    location.href = `/edit/${day}`;
}

function delete_l(lecture) {
    location.href = `/delete/lecture/${lecture}`;
}

function delete_all(lecture) {
    location.href = `/delete/allilectures/${lecture}`;
}

function page_return() {
    location.href = "/return"
}

function settings() {
    location.href = "/settings"
}

function logout() {
    location.href = "/logout"
}