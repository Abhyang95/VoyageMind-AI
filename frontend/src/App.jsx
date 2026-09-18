import { useEffect, useRef, useState } from "react";

import TripForm from "./components/TripForm";
import DestinationDashboard from "./components/DestinationDashboard";
import AuthModal from "./components/AuthModal";
import MyTrips from "./components/MyTrips";
import Favorites from "./components/Favorites";

import API, {
  ACCESS_TOKEN_KEY,
  USER_KEY,
} from "./services/api";

import "./App.css";

const PLANNED_TRIP_KEY = "voyagemind_planned_trip";
const RETURNED_HOME_KEY = "voyagemind_returned_home";

/* ============================================================
   STORAGE HELPERS
   ============================================================ */

const readStorageJSON = (key) => {
  try {
    const value = sessionStorage.getItem(key);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
};

const readStoredUser = () => {
  try {
    const value = localStorage.getItem(USER_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
};

const parseJSONList = (value) => {
  if (Array.isArray(value)) {
    return value;
  }

  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value);

    if (Array.isArray(parsed)) {
      return parsed;
    }
  } catch {
    // Ignore invalid JSON and fall back to comma-separated text.
  }

  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
};

const parseItinerary = (value) => {
  if (!value) {
    return null;
  }

  if (typeof value === "object") {
    return value;
  }

  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

/* ============================================================
   INITIAL JOURNEY
   ============================================================ */

/*
 * Navigation rule:
 *
 * Refresh on #journey
 * -> keep current generated journey.
 *
 * Back to Home
 * -> keep journey available for current session.
 *
 * Refresh Home after returning from Journey
 * -> clear temporary planned journey.
 */

const getInitialPlannedTrip = () => {
  const hash = window.location.hash;

  if (
    (hash === "" || hash === "#home") &&
    sessionStorage.getItem(RETURNED_HOME_KEY) === "1"
  ) {
    sessionStorage.removeItem(PLANNED_TRIP_KEY);
    sessionStorage.removeItem(RETURNED_HOME_KEY);

    return null;
  }

  return readStorageJSON(PLANNED_TRIP_KEY);
};

const getInitialJourneySaved = () => {
  const storedTrip = readStorageJSON(
    PLANNED_TRIP_KEY
  );

  return Boolean(
    storedTrip?.saved_trip_id ||
      storedTrip?.saved_trip?.id
  );
};

const getInitialPage = () => {
  const hash = window.location.hash;

  if (hash === "#journey") {
    return readStorageJSON(PLANNED_TRIP_KEY)
      ? "dashboard"
      : "home";
  }

  if (hash === "#my-trips") {
    return "my-trips";
  }

  if (hash === "#favorites") {
    return "favorites";
  }

  return "home";
};

/* ============================================================
   APP
   ============================================================ */

function App() {
  /* ==========================================================
     IMPORTANT:
     React refs MUST live inside the component.
     ========================================================== */

  const saveLockRef = useRef(false);
  const openJourneyRequestRef = useRef(0);
  const toastTimerRef = useRef(null);

  /* ==========================================================
     MAIN STATE
     ========================================================== */

  const [plannedTrip, setPlannedTrip] = useState(
    getInitialPlannedTrip
  );

  const [currentPage, setCurrentPage] = useState(
    getInitialPage
  );

  const [user, setUser] = useState(
    readStoredUser
  );

  const [authModalOpen, setAuthModalOpen] =
    useState(false);

  const [authLoading, setAuthLoading] =
    useState(true);

  /* ==========================================================
     JOURNEY STATE
     ========================================================== */

  const [journeySaved, setJourneySaved] =
    useState(getInitialJourneySaved);

  const [journeySaving, setJourneySaving] =
    useState(false);

  /* ==========================================================
     FAVORITE STATE
     ========================================================== */

  const [favoriteId, setFavoriteId] =
    useState(null);

  const [favoriteSaving, setFavoriteSaving] =
    useState(false);

  /* ==========================================================
     TOAST STATE
     ========================================================== */

  const [toast, setToast] = useState(null);

  const showToast = (
    message,
    type = "info",
    duration = 3500
  ) => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }

    setToast({
      id: Date.now(),
      message,
      type,
    });

    toastTimerRef.current = setTimeout(() => {
      setToast(null);
      toastTimerRef.current = null;
    }, duration);
  };

  const closeToast = () => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }

    setToast(null);
  };

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  /* ==========================================================
     AUTHENTICATION VERIFICATION
     ========================================================== */

  useEffect(() => {
    let mounted = true;

    const verifyAuthentication = async () => {
      const token = localStorage.getItem(
        ACCESS_TOKEN_KEY
      );

      if (!token) {
        if (mounted) {
          setAuthLoading(false);
        }

        return;
      }

      try {
        const response =
          await API.get("/users/me");

        const authenticatedUser =
          response?.data?.user;

        if (!authenticatedUser) {
          throw new Error(
            "User profile was not returned."
          );
        }

        localStorage.setItem(
          USER_KEY,
          JSON.stringify(authenticatedUser)
        );

        if (mounted) {
          setUser(authenticatedUser);
        }
      } catch (error) {
        console.error(
          "VoyageMind authentication verification failed:",
          error
        );

        localStorage.removeItem(
          ACCESS_TOKEN_KEY
        );

        localStorage.removeItem(
          USER_KEY
        );

        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          setAuthLoading(false);
        }
      }
    };

    verifyAuthentication();

    return () => {
      mounted = false;
    };
  }, []);

  /* ==========================================================
     RESTORE FAVORITE AFTER REFRESH
     ========================================================== */

useEffect(() => {
  if (authLoading || !user || !plannedTrip) {
    return;
  }

  let ignore = false;

  const restoreFavorite = async () => {
    try {
      const destination =
        plannedTrip?.trip?.destination ||
        plannedTrip?.destination?.name ||
        "";

      if (!destination) {
        return;
      }

      const response = await API.get("/favorites/");

      if (ignore) return;

      const favorites =
        response?.data?.favorites || [];

      const destinationKey =
        destination.trim().toLowerCase();

      const matched = favorites.find(
        (favorite) =>
          String(favorite?.destination || "")
            .trim()
            .toLowerCase() === destinationKey
      );

      setFavoriteId(matched?.id || null);
    } catch (error) {
      if (!ignore) {
        console.error(
          "Failed to restore favorite:",
          error
        );
      }
    }
  };

  restoreFavorite();

  return () => {
    ignore = true;
  };
}, [user, plannedTrip, authLoading]);

  /* ==========================================================
     HASH NAVIGATION
     ========================================================== */

  useEffect(() => {
    const handleHashChange = () => {
      const hash =
        window.location.hash;

      /* ------------------------------------------------------
         JOURNEY
         ------------------------------------------------------ */

      if (hash === "#journey") {
        const savedTrip =
          readStorageJSON(
            PLANNED_TRIP_KEY
          );

        if (savedTrip) {
          setPlannedTrip(savedTrip);

          setJourneySaved(
            Boolean(
              savedTrip?.saved_trip_id ||
                savedTrip?.saved_trip?.id
            )
          );

          setCurrentPage("dashboard");

          window.scrollTo({
            top: 0,
            left: 0,
            behavior: "auto",
          });

          return;
        }

        setJourneySaved(false);
        setFavoriteId(null);
        setCurrentPage("home");

        window.scrollTo({
          top: 0,
          left: 0,
          behavior: "auto",
        });

        return;
      }

      /* ------------------------------------------------------
         MY TRIPS
         ------------------------------------------------------ */

      if (hash === "#my-trips") {
        setCurrentPage("my-trips");

        window.scrollTo({
          top: 0,
          left: 0,
          behavior: "auto",
        });

        return;
      }

      /* ------------------------------------------------------
         FAVORITES
         ------------------------------------------------------ */

      if (hash === "#favorites") {
        setCurrentPage("favorites");

        window.scrollTo({
          top: 0,
          left: 0,
          behavior: "auto",
        });

        return;
      }

      /* ------------------------------------------------------
         HOME
         ------------------------------------------------------ */

      setCurrentPage("home");

      window.scrollTo({
        top: 0,
        left: 0,
        behavior: "auto",
      });
    };

    window.addEventListener(
      "hashchange",
      handleHashChange
    );

    return () => {
      window.removeEventListener(
        "hashchange",
        handleHashChange
      );
    };
  }, []);

  /* ==========================================================
     SCROLL
     ========================================================== */

  const scrollTop = () => {
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: "auto",
    });
  };

  /* ==========================================================
     NAVIGATION
     ========================================================== */

  const goHome = () => {
    sessionStorage.setItem(
      RETURNED_HOME_KEY,
      "1"
    );

    window.history.replaceState(
      null,
      "",
      "#home"
    );

    setCurrentPage("home");

    scrollTop();
  };

  const openAuth = () => {
    setAuthModalOpen(true);
  };

  /* ==========================================================
     AUTHENTICATION
     ========================================================== */

  const handleAuthenticated = (
    authenticatedUser
  ) => {
    setUser(authenticatedUser);

    localStorage.setItem(
      USER_KEY,
      JSON.stringify(authenticatedUser)
    );

    setAuthModalOpen(false);

    showToast(
      "Welcome back to VoyageMind.",
      "success"
    );
  };

  const handleLogout = () => {
    localStorage.removeItem(
      ACCESS_TOKEN_KEY
    );

    localStorage.removeItem(
      USER_KEY
    );

    setUser(null);
    setJourneySaved(false);
    setFavoriteId(null);
    setAuthModalOpen(false);

    goHome();
  };

  /* ==========================================================
     MY TRIPS / FAVORITES NAVIGATION
     ========================================================== */

  const openMyTrips = () => {
    if (!user) {
      openAuth();
      return;
    }

    window.history.replaceState(
      null,
      "",
      "#my-trips"
    );

    setCurrentPage("my-trips");

    scrollTop();
  };

  const openFavorites = () => {
    if (!user) {
      openAuth();
      return;
    }

    window.history.replaceState(
      null,
      "",
      "#favorites"
    );

    setCurrentPage("favorites");

    scrollTop();
  };

  /* ==========================================================
     NEW TRIP GENERATED
     ========================================================== */

  const handleTripGenerated = (
    tripResult
  ) => {
    if (!tripResult) {
      return;
    }

    setPlannedTrip(tripResult);

    setJourneySaved(false);

    setFavoriteId(null);

    sessionStorage.removeItem(
      RETURNED_HOME_KEY
    );

    sessionStorage.setItem(
      PLANNED_TRIP_KEY,
      JSON.stringify(tripResult)
    );

    window.history.replaceState(
      null,
      "",
      "#journey"
    );

    setCurrentPage("dashboard");

    scrollTop();
  };

  /* ==========================================================
     REOPEN CURRENT PLANNED TRIP
     ========================================================== */

  const handleViewPlannedTrip = () => {
    const savedTrip =
      readStorageJSON(
        PLANNED_TRIP_KEY
      );

    if (!savedTrip) {
      setPlannedTrip(null);
      setJourneySaved(false);
      setFavoriteId(null);
      setCurrentPage("home");

      return;
    }

    sessionStorage.removeItem(
      RETURNED_HOME_KEY
    );

    setPlannedTrip(savedTrip);

    setJourneySaved(
      Boolean(
        savedTrip?.saved_trip_id ||
          savedTrip?.saved_trip?.id
      )
    );

    setFavoriteId(null);

    window.history.replaceState(
      null,
      "",
      "#journey"
    );

    setCurrentPage("dashboard");

    scrollTop();
  };
  const activeFavoriteId =
  user &&
  plannedTrip &&
  (
    plannedTrip?.trip?.destination ||
    plannedTrip?.destination?.name
  )
    ? favoriteId
    : null;
  /* ==========================================================
     SAVE JOURNEY
     ========================================================== */

  /*
   * Returns:
   *
   * true  -> journey saved successfully / already saved
   * false -> saving failed
   *
   * This is important because Favorites may call saveJourney()
   * before adding the destination to favorites.
   */

  const saveJourney = async () => {
    if (
      saveLockRef.current ||
      journeySaving
    ) {
      return false;
    }

    if (journeySaved) {
      return true;
    }

    if (!plannedTrip) {
      showToast(
        "Generate a journey before saving it.",
        "error"
      );

      return false;
    }

    saveLockRef.current = true;
    setJourneySaving(true);

    try {
      const sourceTrip =
        plannedTrip?.trip || {};

      const itinerary =
        plannedTrip?.itinerary || {};

      const destination =
        sourceTrip.destination ||
        plannedTrip?.destination?.name ||
        plannedTrip?.destination?.city ||
        "Unknown destination";

      const days =
        Number(
          sourceTrip.days ??
            itinerary?.trip_summary
              ?.duration_days ??
            1
        ) || 1;

      const budget =
        Number(
          sourceTrip.budget ??
            itinerary?.budget_plan
              ?.total_budget ??
            0
        ) || 0;

      const currency =
        sourceTrip.currency ||
        itinerary?.budget_plan
          ?.currency ||
        "INR";

      const interests =
        Array.isArray(
          sourceTrip.interests
        )
          ? sourceTrip.interests
          : [];

      const departureDate =
        sourceTrip.departure_date ||
        sourceTrip.departureDate ||
        plannedTrip?.departure_date ||
        plannedTrip?.departureDate ||
        null;

      const returnDate =
        sourceTrip.return_date ||
        sourceTrip.returnDate ||
        plannedTrip?.return_date ||
        plannedTrip?.returnDate ||
        null;

      /* ------------------------------------------------------
         COMPLETE JOURNEY SNAPSHOT
         ------------------------------------------------------ */

      const generatedTripSnapshot = {
        ...plannedTrip,

        trip: {
          ...(plannedTrip?.trip || {}),

          destination,
          days,
          budget,
          currency,

          departure_date:
            departureDate,

          return_date:
            returnDate,

          interests,
        },
      };

      const savedSnapshot = {
        __voyagemind_snapshot: true,

        generated_trip:
          generatedTripSnapshot,
      };

      const itineraryPayload =
        JSON.stringify(
          savedSnapshot
        );

      const payload = {
        destination,

        departure_date:
          departureDate,

        return_date:
          returnDate,

        days,
        budget,
        currency,
        interests,

        itinerary:
          itineraryPayload,
      };

      const response =
        await API.post(
          "/trips/save",
          payload
        );

      const savedTrip =
        response?.data?.trip ||
        response?.data ||
        null;

      const latest = {
        ...generatedTripSnapshot,

        saved_trip_id:
          savedTrip?.id || null,

        saved_trip:
          savedTrip || null,
      };

      setPlannedTrip(latest);
      setJourneySaved(true);

      sessionStorage.setItem(
        PLANNED_TRIP_KEY,
        JSON.stringify(latest)
      );

      showToast(
        response?.data?.created === false
          ? "Journey already saved."
          : "Journey saved successfully.",
        "success"
      );

      return true;
    } catch (error) {
      console.error(
        "Failed to save journey:",
        error
      );

      showToast(
        "Unable to save this journey.",
        "error"
      );

      return false;
    } finally {
      saveLockRef.current = false;
      setJourneySaving(false);
    }
  };

  /* ==========================================================
     FAVORITES TOGGLE
     ========================================================== */

  const toggleFavorite = async () => {
    if (!user) {
      showToast(
        "Please login to manage favorites.",
        "error"
      );

      openAuth();
      return;
    }

    const destination =
      plannedTrip?.trip?.destination ||
      plannedTrip?.destination?.name ||
      "";

    if (!destination) {
      return;
    }

    if (favoriteSaving) {
      return;
    }

    setFavoriteSaving(true);

    try {
      /* ------------------------------------------------------
         REMOVE FAVORITE
         ------------------------------------------------------ */
if (activeFavoriteId) {
  await API.delete(
    `/favorites/${activeFavoriteId}`
  );

  setFavoriteId(null);

  showToast(
    "Removed from favorites.",
    "success"
  );

  return;
}

      /* ------------------------------------------------------
         SAVE JOURNEY FIRST
         ------------------------------------------------------ */

      if (!journeySaved) {
        const saved =
          await saveJourney();

        if (!saved) {
          return;
        }
      }

      /* ------------------------------------------------------
         ADD FAVORITE
         ------------------------------------------------------ */

      const response =
        await API.post(
          "/favorites/",
          {
            destination,
          }
        );

      const favorite =
        response?.data?.favorite ||
        null;

      setFavoriteId(
        favorite?.id || null
      );

      showToast(
        response?.data?.created === false
          ? "Already in favorites."
          : "Added to favorites.",
        "success"
      );
    } catch (error) {
      console.error(
        "Failed to toggle favorite:",
        error
      );

      showToast(
        "Unable to update favorite.",
        "error"
      );
    } finally {
      setFavoriteSaving(false);
    }
  };

  /* ==========================================================
     OPEN SAVED DATABASE JOURNEY
     ========================================================== */

  const viewSavedTrip = async (
    item
  ) => {
    const requestId =
      ++openJourneyRequestRef.current;

    try {
      /* ------------------------------------------------------
         FIND SAVED TRIP
         ------------------------------------------------------ */

      let savedTrip =
        item?.trip ||
        item?.saved_trip ||
        null;

      const tripId =
        item?.trip_id ||
        savedTrip?.id ||
        item?.saved_trip_id ||
        null;

      /*
       * If we already have the complete trip object,
       * don't make another request.
       */

      if (!savedTrip && tripId) {
        const response =
          await API.get(
            `/trips/${tripId}`
          );

        savedTrip =
          response?.data?.trip ||
          null;
      }

      /*
       * Legacy Favorite records may only contain destination.
       */

      if (
        !savedTrip &&
        item?.destination
      ) {
        const response =
          await API.get(
            "/trips/"
          );

        const trips =
          response?.data?.trips ||
          [];

        const destinationKey =
          String(
            item.destination
          )
            .trim()
            .toLowerCase();

        savedTrip =
          trips.find(
            (trip) =>
              String(
                trip?.destination ||
                  ""
              )
                .trim()
                .toLowerCase() ===
              destinationKey
          ) || null;
      }

      if (!savedTrip) {
        throw new Error(
          "Saved journey could not be found."
        );
      }

      /* ------------------------------------------------------
         STALE REQUEST CHECK
         ------------------------------------------------------ */

      if (
        requestId !==
        openJourneyRequestRef.current
      ) {
        return;
      }

      /* ------------------------------------------------------
         PARSE DATABASE SNAPSHOT
         ------------------------------------------------------ */

      let parsedSavedData = null;

      if (savedTrip?.itinerary) {
        try {
          parsedSavedData =
            typeof savedTrip.itinerary ===
            "string"
              ? JSON.parse(
                  savedTrip.itinerary
                )
              : savedTrip.itinerary;
        } catch {
          parsedSavedData = null;
        }
      }

      /* ======================================================
         NEW FORMAT
         COMPLETE JOURNEY SNAPSHOT
         ====================================================== */

      if (
        parsedSavedData
          ?.__voyagemind_snapshot &&
        parsedSavedData
          ?.generated_trip
      ) {
        const generated =
          parsedSavedData.generated_trip;

        const restored = {
          ...generated,

          trip: {
            ...(generated?.trip || {}),

            id: savedTrip.id,

            destination:
              generated?.trip
                ?.destination ||
              savedTrip.destination ||
              "Saved Journey",

            departure_date:
              generated?.trip
                ?.departure_date ||
              savedTrip
                ?.departure_date ||
              null,

            return_date:
              generated?.trip
                ?.return_date ||
              savedTrip
                ?.return_date ||
              null,

            days:
              generated?.trip?.days ??
              savedTrip?.days ??
              1,

            budget:
              generated?.trip?.budget ??
              savedTrip?.budget ??
              0,

            currency:
              generated?.trip
                ?.currency ||
              savedTrip?.currency ||
              "INR",

            interests:
              Array.isArray(
                generated?.trip
                  ?.interests
              )
                ? generated.trip.interests
                : parseJSONList(
                    savedTrip?.interests
                  ),
          },

          saved_trip_id:
            savedTrip.id,

          saved_trip:
            savedTrip,
        };

        setPlannedTrip(restored);
        setJourneySaved(true);

        sessionStorage.setItem(
          PLANNED_TRIP_KEY,
          JSON.stringify(restored)
        );

        sessionStorage.removeItem(
          RETURNED_HOME_KEY
        );

        window.history.replaceState(
          null,
          "",
          "#journey"
        );

        setCurrentPage(
          "dashboard"
        );

        scrollTop();

        return;
      }

      /* ======================================================
         LEGACY FORMAT
         ====================================================== */

      /*
       * Old saved trips only stored the itinerary.
       *
       * Therefore weather, places, distance and validation
       * cannot be reconstructed from the old database row.
       *
       * We regenerate the journey using the saved trip data.
       */

      const legacyItinerary =
        parseItinerary(
          savedTrip?.itinerary
        );

      let regenerated = null;

      try {
        const regenerateResponse =
          await API.post(
            "/plan-trip",
            {
              destination:
                savedTrip?.destination ||
                "Unknown destination",

              days:
                Number(
                  savedTrip?.days || 1
                ) || 1,

              budget:
                Number(
                  savedTrip?.budget || 0
                ) || 0,

              currency:
                savedTrip?.currency ||
                "INR",

              interests:
                parseJSONList(
                  savedTrip?.interests
                ),

              preferences: {
                dining_style:
                  "Moderate",

                hotel_preference:
                  "Mid-range",

                walking: true,
              },

              departure_date:
                savedTrip
                  ?.departure_date ||
                null,

              return_date:
                savedTrip
                  ?.return_date ||
                null,
            }
          );

        regenerated =
          regenerateResponse?.data ||
          null;
      } catch (regenerateError) {
        console.error(
          "Failed to regenerate legacy saved journey:",
          regenerateError
        );
      }

      /* ------------------------------------------------------
         SECOND STALE REQUEST CHECK
         ------------------------------------------------------ */

      if (
        requestId !==
        openJourneyRequestRef.current
      ) {
        return;
      }

      /* ------------------------------------------------------
         BUILD LEGACY RESTORED JOURNEY
         ------------------------------------------------------ */

      const restoredLegacy = {
        ...(regenerated || {}),

        success: true,

        trip: {
          ...(regenerated?.trip || {}),

          id: savedTrip?.id,

          destination:
            regenerated?.trip
              ?.destination ||
            savedTrip?.destination ||
            "Saved Journey",

          departure_date:
            regenerated?.trip
              ?.departure_date ||
            savedTrip
              ?.departure_date ||
            null,

          return_date:
            regenerated?.trip
              ?.return_date ||
            savedTrip
              ?.return_date ||
            null,

          days:
            regenerated?.trip?.days ??
            savedTrip?.days ??
            1,

          budget:
            regenerated?.trip?.budget ??
            savedTrip?.budget ??
            0,

          currency:
            regenerated?.trip
              ?.currency ||
            savedTrip?.currency ||
            "INR",

          interests:
            Array.isArray(
              regenerated?.trip
                ?.interests
            )
              ? regenerated.trip.interests
              : parseJSONList(
                  savedTrip?.interests
                ),

          itinerary:
            regenerated?.trip
              ?.itinerary ||
            legacyItinerary ||
            null,
        },

        destination: {
          ...(regenerated?.destination ||
            {}),

          name:
            regenerated?.destination
              ?.name ||
            savedTrip?.destination ||
            "Saved Journey",
        },

        weather:
          regenerated?.weather ||
          {},

        places:
          regenerated?.places ||
          [],

        itinerary:
          regenerated?.itinerary ||
          legacyItinerary ||
          {},

        distance:
          regenerated?.distance ||
          {},

        validation:
          regenerated?.validation ||
          {},

        reflection:
          regenerated?.reflection ||
          {},

        saved_trip_id:
          savedTrip?.id ||
          null,

        saved_trip:
          savedTrip,
      };

      setPlannedTrip(
        restoredLegacy
      );

      setJourneySaved(
        Boolean(savedTrip?.id)
      );

      /*
       * IMPORTANT:
       *
       * We keep the restored journey in sessionStorage so
       * refreshing #journey does not immediately lose it.
       */

      sessionStorage.setItem(
        PLANNED_TRIP_KEY,
        JSON.stringify(
          restoredLegacy
        )
      );

      sessionStorage.removeItem(
        RETURNED_HOME_KEY
      );

      window.history.replaceState(
        null,
        "",
        "#journey"
      );

      setCurrentPage(
        "dashboard"
      );

      scrollTop();
    } catch (error) {
      console.error(
        "Failed to open saved journey:",
        error
      );

      showToast(
        "Unable to open this saved journey.",
        "error"
      );
    }
  };

  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <div className="app-root">

      {/* =====================================================
          HOME
          ===================================================== */}

      {currentPage === "home" && (
        <TripForm
          onTripGenerated={
            handleTripGenerated
          }

          hasPlannedTrip={
            Boolean(plannedTrip)
          }

          onViewPlannedTrip={
            handleViewPlannedTrip
          }

          user={user}

          authLoading={
            authLoading
          }

          onOpenAuth={
            openAuth
          }

          onLogout={
            handleLogout
          }

          onOpenMyTrips={
            openMyTrips
          }

          onOpenFavorites={
            openFavorites
          }
        />
      )}

      {/* =====================================================
          DESTINATION DASHBOARD
          ===================================================== */}

      {currentPage ===
        "dashboard" &&
        plannedTrip && (
          <DestinationDashboard
            result={
              plannedTrip
            }

            onBack={
              goHome
            }

            onSaveJourney={
              saveJourney
            }

            journeySaved={
              journeySaved
            }

            journeySaving={
              journeySaving
            }

            onToggleFavorite={
              toggleFavorite
            }

            favoriteSaving={
              favoriteSaving
            }

            isFavorite={
  Boolean(
    activeFavoriteId
  )
}
          />
        )}

      {/* =====================================================
          MY TRIPS
          ===================================================== */}

      {currentPage ===
        "my-trips" && (
        <MyTrips
          onBack={
            goHome
          }

          onViewTrip={
            viewSavedTrip
          }
        />
      )}

      {/* =====================================================
          FAVORITES
          ===================================================== */}

      {currentPage ===
        "favorites" && (
        <Favorites
          onBack={
            goHome
          }

          onViewTrip={
            viewSavedTrip
          }
        />
      )}

      {/* =====================================================
          AUTH MODAL
          ===================================================== */}

      <AuthModal
        isOpen={
          authModalOpen
        }

        onClose={() =>
          setAuthModalOpen(false)
        }

        onAuthenticated={
          handleAuthenticated
        }
      />

      {/* =====================================================
          VOYAGEMIND TOAST
          ===================================================== */}

      {toast && (
        <div
          className={`vm-toast vm-toast-${toast.type}`}
          role="status"
          aria-live="polite"
        >
          <div className="vm-toast-icon">
            {toast.type ===
              "success" && "✓"}

            {toast.type ===
              "error" && "!"}

            {toast.type ===
              "warning" && "!"}

            {toast.type ===
              "info" && "i"}
          </div>

          <div className="vm-toast-content">
            <strong>
              {toast.type ===
              "success"
                ? "VoyageMind"
                : toast.type ===
                  "error"
                ? "Action Required"
                : "VoyageMind"}
            </strong>

            <span>
              {toast.message}
            </span>
          </div>

          <button
            type="button"
            className="vm-toast-close"
            onClick={
              closeToast
            }
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;