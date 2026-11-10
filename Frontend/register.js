
let form = document.getElementById("registerForm");

form.addEventListener("submit", function(event) {

    event.preventDefault();

    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let confirmPassword = document.getElementById("confirmPassword").value;

    let message = document.getElementById("message");

    if (password.length < 8) {
        message.innerHTML = "Minimum 8 characters required";
    }

    else if (!/[A-Z]/.test(password)) {
        message.innerHTML = "Add one uppercase letter";
    }

    else if (!/[a-z]/.test(password)) {
        message.innerHTML = "Add one lowercase letter";
    }

    else if (!/[0-9]/.test(password)) {
        message.innerHTML = "Add one number";
    }

    else if (!/[!@#$%^&*(),.?":{}|_+=-]/.test(password)) {
        message.innerHTML = "Add one special character";
    }

    else if (password !== confirmPassword) {
        message.innerHTML = "Passwords do not match";
    }

    else {
        message.style.color = "green";
        message.innerHTML = "Registration successful!";
    }

});
