// ==========================================
// CONFIGURATION
// ==========================================

const API_BASE_URL = "http://127.0.0.1:8000";

console.log("Animal Rescue JavaScript loaded successfully.");


// ==========================================
// COMMON API REQUEST FUNCTION
// ==========================================
// ==========================================
// FETCH EMERGENCY SEARCH RESULTS
// ==========================================

async function pollEmergencySearch(incidentId, result) {
    const statusMessage = document.createElement("p");

    statusMessage.textContent =
        "Emergency report saved! Searching for nearby veterinary clinics...";

    result.appendChild(statusMessage);

    // Check for results every 3 seconds, for up to 3 minutes.
    for (let attempt = 0; attempt < 60; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 3000));

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/emergency/search/${encodeURIComponent(incidentId)}`
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Unable to retrieve clinic results."
                );
            }

            if (
                data.vet_search_status === "searching" ||
                data.vet_search_status === "queued"
            ) {
                statusMessage.textContent =
                    "Report saved. Still searching for nearby veterinary clinics...";
                continue;
            }

            if (data.vet_search_status === "completed") {
                statusMessage.textContent =
                    "Veterinary search completed.";

                const heading = document.createElement("h3");
                heading.textContent = "Nearby Veterinary Clinics";
                result.appendChild(heading);

                const searchData = data.live_vets_scraped;

                let searchText = "";

                if (typeof searchData === "string") {
                    searchText = searchData;
                } else if (searchData) {
                    const nested = searchData.result?.result;

                    if (typeof nested === "string") {
                        searchText = nested;
                    } else if (
                        typeof searchData.result?.content === "string"
                    ) {
                        searchText = searchData.result.content;
                    } else {
                        searchText = JSON.stringify(searchData, null, 2);
                    }
                }

                const output = document.createElement("pre");

                output.style.whiteSpace = "pre-wrap";
                output.style.overflowWrap = "anywhere";
                output.textContent = searchText ||
                    "The search completed, but no clinic details were returned.";

                result.appendChild(output);

                const disclaimer = document.createElement("p");
                disclaimer.className = "disclaimer";
                disclaimer.textContent =
                    "Please call the clinic to confirm its opening hours " +
                    "and availability. Search results may not be current.";

                result.appendChild(disclaimer);

                result.className = "result visible success";
                return;
            }

            if (
                data.vet_search_status === "failed" ||
                data.vet_search_status === "not_configured"
            ) {
                statusMessage.textContent =
                    data.error ||
                    "The report was saved, but the veterinary search failed.";

                result.className = "result visible success";
                return;
            }

            statusMessage.textContent =
                "Report saved. Waiting for search results...";
        } catch (error) {
            console.error("Clinic search polling error:", error);

            statusMessage.textContent =
                "Your report is saved, but we couldn't retrieve the clinic results. " +
                "Please try checking again later.";

            result.className = "result visible success";
            return;
        }
    }

    statusMessage.textContent =
        "Your emergency report is saved (Report ID: " + incidentId + "). " +
        "The clinic search is taking longer than expected. " +
        "Please check again later.";

    result.className = "result visible success";
}
async function sendRequest(endpoint, payload, resultId) {
    const result = document.getElementById(resultId);

    if (!result) {
        console.error(`Result element not found: ${resultId}`);
        return;
    }

    result.className = "result visible";
    result.textContent = "Please wait... Processing your request.";

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const responseText = await response.text();

        let data;

        try {
            data = JSON.parse(responseText);
        } catch {
            data = { message: responseText };
        }

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : JSON.stringify(data.detail || data)
            );
        }

        // Clear the previous result.
        result.replaceChildren();

        // Create the appropriate heading.
        const heading = document.createElement("h3");

        if (endpoint === "/api/ai/first-aid") {
            heading.textContent = "First-Aid Guidance";
        } else if (endpoint === "/api/routine/allocate") {
            heading.textContent = "Animal Care Recommendations";
        } else {
            heading.textContent = "Emergency Report Confirmation";
        }

        result.appendChild(heading);


        // ==========================================
        // AI FIRST-AID RESULTS
        // ==========================================

        if (endpoint === "/api/ai/first-aid") {
            const guidance = document.createElement("div");

            guidance.style.whiteSpace = "pre-wrap";
            guidance.textContent =
                data.guidance || "No guidance was returned.";

            result.appendChild(guidance);

            if (data.disclaimer) {
                const disclaimer = document.createElement("p");

                disclaimer.className = "disclaimer";
                disclaimer.textContent = data.disclaimer;

                result.appendChild(disclaimer);
            }
        }


        // ==========================================
        // FIND A VET / NGO RESULTS
        // ==========================================

        else if (endpoint === "/api/routine/allocate") {
            const facilities = data.allocated_facilities || [];
if (facilities.length === 0) {
    const message = document.createElement("p");

    message.textContent =
        data.message ||
        "No facility details were found. Please contact a local animal rescue organisation.";

    result.appendChild(message);

    if (data.search_details) {
        const output = document.createElement("pre");

        output.style.whiteSpace = "pre-wrap";
        output.style.overflowWrap = "anywhere";
        output.textContent = data.search_details;

        result.appendChild(output);
    }
}
             else {
                facilities.forEach(function (facility) {
                    const card = document.createElement("div");

                    card.className = "facility-card";

                    const name = document.createElement("h4");

                    name.textContent =
                        facility.name || "Animal care facility";

                    card.appendChild(name);

                                         const details = [
    ["Type", facility.type],
    ["Location", facility.location],
    ["Contact", facility.contact],
    ["Status", facility.status],
    ["Details", facility.details]
];

details.forEach(function ([label, value]) {
    if (value) {
        const paragraph = document.createElement("p");
        paragraph.textContent = `${label}: ${value}`;
        card.appendChild(paragraph);
    }
});

if (facility.source_url) {
    try {
        const sourceUrl = new URL(facility.source_url);

        if (sourceUrl.protocol === "https:" ||
            sourceUrl.protocol === "http:") {
            const link = document.createElement("a");

            link.href = sourceUrl.href;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "View source / website";

            card.appendChild(link);
        }
    } catch (error) {
        console.warn("Invalid facility source URL");
    }
}

                    details.forEach(function ([label, value]) {
                        if (value) {
                            const paragraph = document.createElement("p");

                            paragraph.textContent = `${label}: ${value}`;

                            card.appendChild(paragraph);
                        }
                    });

                    result.appendChild(card);
                });
            }
        }


        // ==========================================
        // EMERGENCY RESCUE RESULTS
        // ==========================================

        else {
            const message = document.createElement("p");

            message.textContent = data.success
                ? "Your emergency report was submitted successfully."
                : "Please check the report status.";

            result.appendChild(message);

            if (data.incident_id !== undefined) {
                const reportId = document.createElement("p");

                reportId.textContent = `Report ID: ${data.incident_id}`;

                result.appendChild(reportId);
            }

            if (
                data.incident_id !== undefined &&
                (
                    data.vet_search_status === "searching" ||
                    data.vet_search_status === "queued" ||
                    !data.vet_search_status
                )
            ) {
                await pollEmergencySearch(data.incident_id, result);
            } else if (data.live_vets_scraped) {
                const output = document.createElement("pre");

                output.style.whiteSpace = "pre-wrap";
                output.style.overflowWrap = "anywhere";

                const searchData = data.live_vets_scraped;

                let searchText = "";

                if (typeof searchData === "string") {
                    searchText = searchData;
                } else {
                    const nested = searchData.result?.result;

                    if (typeof nested === "string") {
                        searchText = nested;
                    } else if (typeof searchData.result?.content === "string") {
                        searchText = searchData.result.content;
                    } else {
                        searchText = JSON.stringify(searchData, null, 2);
                    }
                }

                output.textContent = searchText;
                result.appendChild(output);

                const disclaimer = document.createElement("p");
                disclaimer.className = "disclaimer";
                disclaimer.textContent =
                    "Please call the clinic to confirm its opening hours and availability.";
                result.appendChild(disclaimer);
            } else if (data.vet_search_status === "completed") {
                await pollEmergencySearch(data.incident_id, result);
            } else if (data.vet_search_status === "failed") {
                const warning = document.createElement("p");

                warning.textContent =
                    "Your report was saved, but the clinic search failed.";

                result.appendChild(warning);
            }
        }
        result.className = "result visible success";

    } catch (error) {
        console.error(`Request failed for ${endpoint}:`, error);

        result.className = "result visible error";

        result.textContent =
            "We couldn't complete your request. " +
            error.message +
            ". Please try again or contact a local animal-care professional.";
    }
}
// ==========================================
// PRESERVE EMERGENCY PAGE STATE
// ==========================================

const emergencyFieldIds = [
    "animalType",
    "latitude",
    "longitude",
    "emergencyDescription"
];

const emergencyStorageKey = "pawrescue_emergency_state";

// Clear saved state if the user manually refreshes this page.
const navigationEntry = performance.getEntriesByType("navigation")[0];

if (navigationEntry && navigationEntry.type === "reload") {
    sessionStorage.removeItem(emergencyStorageKey);
}

const emergencyResultBox =
    document.getElementById("emergencyResult");

// Restore previously saved form fields and results.
try {
    const savedState = JSON.parse(
        sessionStorage.getItem(emergencyStorageKey) || "null"
    );

    if (savedState) {
        emergencyFieldIds.forEach(function (id) {
            const field = document.getElementById(id);

            if (field && savedState.fields) {
                field.value = savedState.fields[id] ?? "";
            }
        });

        if (emergencyResultBox && savedState.resultHTML !== undefined) {
            emergencyResultBox.innerHTML = savedState.resultHTML;
            emergencyResultBox.className =
                savedState.resultClass || "result";
        }
    }
} catch (error) {
    console.error("Could not restore emergency state:", error);
}

// Save the current form fields and results.
function saveEmergencyState() {
    const fields = {};

    emergencyFieldIds.forEach(function (id) {
        const field = document.getElementById(id);

        if (field) {
            fields[id] = field.value;
        }
    });

    sessionStorage.setItem(
        emergencyStorageKey,
        JSON.stringify({
            fields: fields,
            resultHTML: emergencyResultBox
                ? emergencyResultBox.innerHTML
                : "",
            resultClass: emergencyResultBox
                ? emergencyResultBox.className
                : "result"
        })
    );
}

// Save changes to the form as the user types.
emergencyFieldIds.forEach(function (id) {
    const field = document.getElementById(id);

    if (field) {
        field.addEventListener("input", saveEmergencyState);
        field.addEventListener("change", saveEmergencyState);
    }
});

// Save changes whenever emergency results update.
if (emergencyResultBox) {
    const resultObserver = new MutationObserver(function () {
        saveEmergencyState();
    });

    resultObserver.observe(emergencyResultBox, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true
    });
}

// Save before navigating away from the page.
window.addEventListener("pagehide", saveEmergencyState);

// ==========================================
// EMERGENCY RESCUE FORM
// ==========================================

const emergencyForm = document.getElementById("emergencyForm");

if (emergencyForm) {
    emergencyForm.addEventListener("submit", function (event) {
        event.preventDefault();

        sendRequest(
            "/api/emergency/broadcast",
            {
                animal_type:
                    document.getElementById("animalType").value,

                latitude: Number(
                    document.getElementById("latitude").value
                ),

                longitude: Number(
                    document.getElementById("longitude").value
                ),

                injury_description:
                    document.getElementById("emergencyDescription")
                        .value.trim()
            },
            "emergencyResult"
        );
    });
}


// ==========================================
// GET USER'S LOCATION
// ==========================================

const locationButton = document.getElementById("locationButton");

if (locationButton) {
    locationButton.addEventListener("click", function () {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by this browser.");
            return;
        }

        locationButton.textContent = "Getting location...";
        locationButton.disabled = true;

        navigator.geolocation.getCurrentPosition(
            function (position) {
                document.getElementById("latitude").value =
                    position.coords.latitude;

                document.getElementById("longitude").value =
                    position.coords.longitude;

                locationButton.textContent = "Location detected";
                locationButton.disabled = false;
            },

            function (error) {
                let message =
                    "Location unavailable. Please enter the coordinates manually.";

                if (error.code === 1) {
                    message =
                        "Location permission was denied. Allow location access in your browser settings and try again.";
                } else if (error.code === 2) {
                    message =
                        "Your location could not be determined. Check your device's location settings and try again.";
                } else if (error.code === 3) {
                    message =
                        "Location detection timed out. Please try again.";
                }

                alert(message);

                locationButton.textContent = "Use My Location";
                locationButton.disabled = false;

                console.error("Geolocation error:", error.message);
            },

            {
                enableHighAccuracy: false,
                timeout: 15000,
                maximumAge: 60000
            }
        );
    });
}


// ==========================================
// FIND ANIMAL CARE FORM
// ==========================================

const routineForm = document.getElementById("routineForm");

if (routineForm) {
    routineForm.addEventListener("submit", function (event) {
        event.preventDefault();

        console.log("ROUTINE FORM SUBMITTED");

        sendRequest(
            "/api/routine/allocate",
            {
                location_name:
                    document.getElementById("locationName").value.trim(),

                pet_type:
                    document.getElementById("petType").value,

                condition:
                    document.getElementById("condition").value
            },
            "routineResult"
        );
    });
}



// ==========================================
// AI FIRST-AID FORM
// ==========================================

const firstAidForm = document.getElementById("firstAidForm");

if (firstAidForm) {
    firstAidForm.addEventListener("submit", function (event) {
        event.preventDefault();

        sendRequest(
            "/api/ai/first-aid",
            {
                injury_description:
                    document.getElementById("injuryDescription")
                        .value.trim()
            },
            "firstAidResult"
        );
    });
}
