document.getElementById("person-image").addEventListener("change", function(event) {
    const personPreview = document.getElementById("person-preview");
    personPreview.src = URL.createObjectURL(event.target.files[0]);
    personPreview.style.display = "block";
});

document.getElementById("garment-image").addEventListener("change", function(event) {
    const garmentPreview = document.getElementById("garment-preview");
    garmentPreview.src = URL.createObjectURL(event.target.files[0]);
    garmentPreview.style.display = "block";
});

document.getElementById("tryon-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("person_image", document.getElementById("person-image").files[0]);
    formData.append("garment_image", document.getElementById("garment-image").files[0]);
    formData.append("garment_desc", document.getElementById("garment-desc").value);

    // Show loading spinner
    document.getElementById("loading").style.display = "block";
    document.getElementById("result").style.display = "none";

    try {
        const response = await fetch("/try-on", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        // Hide loading spinner
        document.getElementById("loading").style.display = "none";

        if (result.error) {
            // Display error message if there's an error field in the response
            alert(result.error);
        } else if (result.output_image && result.masked_image) {
            // Show the result images
            document.getElementById("output-image").src = result.output_image;
            document.getElementById("masked-image").src = result.masked_image;
            document.getElementById("result").style.display = "block";
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while processing the try-on.");
        // Hide loading spinner
        document.getElementById("loading").style.display = "none";
    }
});
