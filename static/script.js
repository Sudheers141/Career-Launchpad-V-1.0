document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("applicationForm").onsubmit = async function (event) {
        event.preventDefault();

        const company = document.getElementById("company").value;
        const jobTitle = document.getElementById("job_title").value;
        const jobDescription = document.getElementById("job_description").value;
        const resumeText = document.getElementById("resume_text").value;
        const resumeFile = document.getElementById("resume_file").files[0];

        if (!resumeText && !resumeFile) {
            alert("Please provide either Resume Text or upload a Resume file.");
            return;
        }

        const formData = new FormData();
        formData.append("company", company);
        formData.append("job_title", jobTitle);
        formData.append("job_description", jobDescription);
        formData.append("resume_text", resumeText);

        if (resumeFile) {
            formData.append("resume_file", resumeFile);
        }

        try {
            const response = await fetch("/submit_application", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Network response was not ok.");
            }

            const result = await response.json();

            document.getElementById("match-score").textContent = `${result.match_score} / 100`;

            // Display feedback
            const feedbackDiv = document.getElementById("feedback");
            feedbackDiv.innerHTML = formatFeedback(result.feedback);

            // Display suggestions in a detailed sentence format
            const suggestionsDiv = document.getElementById("suggestions");
            suggestionsDiv.innerHTML = formatDetailedSuggestions(result.suggestions);

        } catch (error) {
            console.error("Error during submission:", error);
            document.getElementById("response").innerHTML = `<p>There was an error processing your request. Check console for details.</p>`;
        }
    };

    function formatFeedback(feedback) {
        let feedbackHtml = `<p><strong>Assessment:</strong> ${feedback.overall_match.assessment}</p>`;

        if (feedback.keywords_analysis.missing_keywords.length > 0) {
            feedbackHtml += `<p><strong>Missing Keywords:</strong> ${feedback.keywords_analysis.missing_keywords.join(", ")}</p>`;
        }

        if (feedback.detailed_recommendations.length > 0) {
            feedbackHtml += `<p><strong>Detailed Recommendations:</strong></p><ul>`;
            feedback.detailed_recommendations.forEach(rec => {
                feedbackHtml += `<li>${rec}</li>`;
            });
            feedbackHtml += `</ul>`;
        }

        return feedbackHtml;
    }

    function formatDetailedSuggestions(suggestions) {
        let suggestionsHtml = `<p><strong>Suggestions:</strong></p><ul>`;
        suggestions.forEach(suggestion => {
            suggestionsHtml += `<li>${suggestion}</li>`;
        });
        suggestionsHtml += `</ul>`;
        return suggestionsHtml;
    }

    function clearField(fieldId) {
        document.getElementById(fieldId).value = "";
    }

    function clearForm() {
        document.getElementById("applicationForm").reset();
    }
});
