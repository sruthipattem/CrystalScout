let loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", function(event) {
    event.preventDefault();

    let email = document.getElementById("email").value.trim();
    let password = document.getElementById("password").value;
    let message = document.getElementById("loginMessage");

    if (email === "" || password === "") {
        message.textContent = "Please enter both your email and password.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        message.textContent = "Please enter a valid email address.";
    } else {
        // This is a frontend demonstration, not account authentication.
        window.location.href = "dashboard.html";
    }
});
