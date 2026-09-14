import { useState } from "react";
import TripForm from "./components/TripForm";
import DestinationDashboard from "./components/DestinationDashboard";

const STORAGE_KEY = "voyagemind_planned_trip";
const RETURNED_HOME_KEY = "voyagemind_returned_home";

function getSavedTrip() {
  try {
    const savedTrip = sessionStorage.getItem(STORAGE_KEY);

    if (!savedTrip) {
      return null;
    }

    const parsedTrip = JSON.parse(savedTrip);

    return parsedTrip?.success ? parsedTrip : null;
  } catch (error) {
    console.error(
      "Unable to restore saved VoyageMind journey:",
      error
    );

    sessionStorage.removeItem(STORAGE_KEY);

    return null;
  }
}

function getInitialPage() {
  const hash = window.location.hash;

  /*
   * If the user is on the Home page and had previously
   * clicked "Back to Home", then a refresh should start
   * a completely fresh planner.
   */
  if (hash === "#home") {
    const returnedHome =
      sessionStorage.getItem(RETURNED_HOME_KEY) === "true";

    if (returnedHome) {
      sessionStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(RETURNED_HOME_KEY);

      return "home";
    }

    return "home";
  }

  /*
   * If the browser is on the generated journey URL,
   * restore the existing journey.
   */
  if (hash === "#journey") {
    return "dashboard";
  }

  /*
   * Default page.
   */
  return "home";
}

function App() {
  /*
   * Determine the page BEFORE restoring the journey.
   */
  const [currentPage, setCurrentPage] = useState(
    getInitialPage
  );

  /*
   * Restore the saved journey.
   *
   * If getInitialPage() detected that we were returning
   * to Home and refreshing, the saved journey has already
   * been removed.
   */
  const [plannedTrip, setPlannedTrip] = useState(
    getSavedTrip
  );

  /*
   * ==========================================
   * CREATE NEW JOURNEY
   * ==========================================
   */
  const handleTripGenerated = (tripResult) => {
    if (!tripResult?.success) {
      return;
    }

    /*
     * Save the new journey in React state.
     */
    setPlannedTrip(tripResult);

    /*
     * Persist the journey for refresh.
     */
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(tripResult)
      );

      /*
       * We are no longer in the "returned home" state.
       */
      sessionStorage.removeItem(RETURNED_HOME_KEY);
    } catch (error) {
      console.warn(
        "Unable to save VoyageMind journey:",
        error
      );
    }

    /*
     * Move to generated journey page.
     */
    window.history.replaceState(
      null,
      "",
      "#journey"
    );

    setCurrentPage("dashboard");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  /*
   * ==========================================
   * DASHBOARD → HOME
   * ==========================================
   */
  const handleBackToHome = () => {
    /*
     * IMPORTANT:
     *
     * DO NOT delete plannedTrip here.
     *
     * This allows:
     *
     * Dashboard
     *     ↓
     * Back to Home
     *     ↓
     * View Planned Trip
     *
     * to work without regenerating anything.
     */
    try {
      sessionStorage.setItem(
        RETURNED_HOME_KEY,
        "true"
      );
    } catch (error) {
      console.warn(
        "Unable to save home navigation state:",
        error
      );
    }

    /*
     * Change URL to Home.
     */
    window.history.replaceState(
      null,
      "",
      "#home"
    );

    setCurrentPage("home");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  /*
   * ==========================================
   * HOME → VIEW PLANNED TRIP
   * ==========================================
   */
  const handleViewPlannedTrip = () => {
    if (!plannedTrip) {
      return;
    }

    /*
     * We are viewing the existing journey again,
     * so this is no longer a "returned home" state.
     */
    try {
      sessionStorage.removeItem(RETURNED_HOME_KEY);
    } catch (error) {
      console.warn(
        "Unable to update VoyageMind navigation state:",
        error
      );
    }

    /*
     * Change URL to journey.
     */
    window.history.replaceState(
      null,
      "",
      "#journey"
    );

    /*
     * Open the SAME saved dashboard.
     *
     * No:
     * - API request
     * - Places search
     * - Weather request
     * - Gemini request
     */
    setCurrentPage("dashboard");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <div className="app">
      {currentPage === "home" && (
        <TripForm
          onTripGenerated={handleTripGenerated}
          hasPlannedTrip={Boolean(plannedTrip)}
          onViewPlannedTrip={handleViewPlannedTrip}
        />
      )}

      {currentPage === "dashboard" && plannedTrip && (
        <DestinationDashboard
          result={plannedTrip}
          onBack={handleBackToHome}
        />
      )}

      {/*
       * Safety fallback:
       *
       * If someone manually opens #journey but there
       * is no saved journey, show the planner.
       */}
      {currentPage === "dashboard" && !plannedTrip && (
        <TripForm
          onTripGenerated={handleTripGenerated}
          hasPlannedTrip={false}
          onViewPlannedTrip={handleViewPlannedTrip}
        />
      )}
    </div>
  );
}

export default App;