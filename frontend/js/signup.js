document.getElementById("signupForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const dob = document.getElementById("dob").value;
    const password = document.getElementById("password").value;

    const user = {
        username: username,
        email: email,
        dob: dob,
        password: password
    };

    const response = await fetch("http://localhost:8000/user/newaccount", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(user)
    });

    if (response.ok) {
        alert("Account created successfully. Please log in.");
        window.location.href = "./login.html";
    } else {
        const errorData = await response.json();
        alert(errorData.detail || "An error occurred.");
    }
});
