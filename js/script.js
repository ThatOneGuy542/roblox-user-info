document.getElementById("cookieForm").addEventListener("submit", function(event) {
    const cookieInput = document.getElementById("cookie").value.trim();
    if (!cookieInput) {
        event.preventDefault();
        alert("Please enter a valid .ROBLOSECURITY cookie.");
    }
});
