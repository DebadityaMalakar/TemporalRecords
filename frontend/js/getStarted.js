window.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("yes").addEventListener("click", () => {
        window.location.href = "./login.html";
    });

    document.getElementById("no").addEventListener("click", () => {
        document.getElementById("part1").style.display = "none";
        document.getElementById("part2").style.display = "block";
    });

    document.getElementById("yesp2").addEventListener("click", () => {
        window.location.href = "./signup.html";
    });

    document.getElementById("nop3").addEventListener("click", () => {
        document.getElementById("part2").style.display = "none";
        document.getElementById("part3").style.display = "block";
        createAnonymousAccount();
    });
});

async function createAnonymousAccount() {
    const username = `Anonymous_${Math.random().toString(36).substring(2, 8)}`;
    const password = Math.random().toString(36).substring(2, 12);
    const dob = new Date();
    dob.setFullYear(dob.getFullYear() - 18);
    const formattedDob = dob.toISOString().split('T')[0]; // Format: YYYY-MM-DD

    const user = {
        username: username,
        email: `${username}@example.com`,
        dob: formattedDob,
        password: password,
    };

    // Create the user in the backend
    try {
        const response = await fetch("http://localhost:8000/user/newaccount", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(user),
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById("accountDetails").innerHTML = `
                <p><strong>Username:</strong> ${data.username}</p>
                <p><strong>Password:</strong> ${password}</p>
            `;
            localStorage.setItem("user_id", data.id);  // Store user ID in local storage
            document.getElementById("goToDashboard").addEventListener("click", () => {
                window.location.href = `./dashboard.html?id=${data.id}`;
            });
        } else {
            const errorData = await response.json();  // Capture error response
            document.getElementById("accountDetails").innerText = `Error creating anonymous account: ${errorData.detail || 'Unknown error.'}`;
        }
    } catch (error) {
        document.getElementById("accountDetails").innerText = `Network error: ${error.message}`;
    }
}
