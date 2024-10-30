window.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const userId = localStorage.getItem("user_id");

    try {
        // Fetch user details if logged in
        if (token && userId) {
            const userResponse = await fetch(`http://localhost:8000/user/details/${userId}`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!userResponse.ok) {
                throw new Error("Failed to fetch user details");
            }

            const userData = await userResponse.json();
            document.getElementById("userDetails").innerHTML = `
                <p>Name: ${userData.name}</p>
                <p>Username: ${userData.username}</p>
                <p>Email: ${userData.email}</p>
            `;
        }

        // Determine whether to fetch all records or only public records
        const privacy = token ? "true" : "false";  // true for logged in users, false for guests

        // Fetch records
        const recordsResponse = await fetch(`http://localhost:8000/records/${userId}?privacy=${privacy}`, {
            method: "GET",
            headers: {
                "Authorization": token ? `Bearer ${token}` : undefined
            }
        });

        if (!recordsResponse.ok) {
            throw new Error("Failed to fetch records");
        }

        const recordsData = await recordsResponse.json();
        const recordsDiv = document.getElementById("records");

        if (recordsData.length === 0) {
            recordsDiv.innerHTML = "<p>No records found.</p>";
        } else {
            recordsDiv.innerHTML = recordsData.map(record => `
                <div class="uk-card uk-card-default uk-card-body uk-margin">
                    <h3 class="uk-card-title">${record.title}</h3>
                    <p>${record.body}</p>
                    <p><strong>Date:</strong> ${record.date}</p>
                    <p><strong>Time:</strong> ${record.time}</p>
                </div>
            `).join("");
        }
    } catch (error) {
        console.error(error);
        alert("An error occurred while fetching data.");
    }

    document.getElementById("logoutButton").onclick = function() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_id");
        window.location.href = "./login.html";
    };
});
