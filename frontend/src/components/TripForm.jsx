import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import API from "../services/api";
import "./TripForm.css";
import heroImage from "../assets/hero.png";

const INTERESTS = [
  {
    id: "architecture",
    label: "Architecture",
    icon: "🕌",
  },
  {
    id: "history",
    label: "History",
    icon: "🏺",
  },
  {
    id: "food",
    label: "Food",
    icon: "🍜",
  },
  {
    id: "nightlife",
    label: "Nightlife",
    icon: "🌃",
  },
  {
    id: "museums",
    label: "Museums",
    icon: "🏛️",
  },
  {
    id: "nature",
    label: "Nature",
    icon: "🌿",
  },
  {
    id: "shopping",
    label: "Shopping",
    icon: "🛒",
  },
  {
    id: "adventure",
    label: "Adventure",
    icon: "🏄",
  },
];

const CURRENCY_OPTIONS = [
  {
    code: "INR",
    symbol: "₹",
    name: "Indian Rupee",
  },
  {
    code: "USD",
    symbol: "$",
    name: "US Dollar",
  },
  {
    code: "EUR",
    symbol: "€",
    name: "Euro",
  },
  {
    code: "GBP",
    symbol: "£",
    name: "British Pound",
  },
  {
    code: "JPY",
    symbol: "¥",
    name: "Japanese Yen",
  },
  {
    code: "AED",
    symbol: "د.إ",
    name: "UAE Dirham",
  },
  {
    code: "SGD",
    symbol: "S$",
    name: "Singapore Dollar",
  },
  {
    code: "CAD",
    symbol: "C$",
    name: "Canadian Dollar",
  },
  {
    code: "AUD",
    symbol: "A$",
    name: "Australian Dollar",
  },
];

const formatCurrency = (
  amount,
  currency
) => {
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount)) {
    return "—";
  }

  try {
    return new Intl.NumberFormat(
      undefined,
      {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }
    ).format(numericAmount);
  } catch {
    return `${currency} ${Math.round(
      numericAmount
    ).toLocaleString()}`;
  }
};

/* -------------------------------------------------------
   DATE HELPERS
------------------------------------------------------- */

const calculateTripDays = (
  departureDate,
  returnDate
) => {
  if (!departureDate || !returnDate) {
    return 0;
  }

  const departure = new Date(
    `${departureDate}T00:00:00`
  );

  const returnDay = new Date(
    `${returnDate}T00:00:00`
  );

  const difference =
    returnDay - departure;

  return Math.max(
    0,
    Math.round(
      difference / 86400000
    )
  );
};

const formatDatePreview = (date) => {
  if (!date) {
    return "Select a date";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    }
  ).format(
    new Date(`${date}T00:00:00`)
  );
};

/* -------------------------------------------------------
   COMPONENT
------------------------------------------------------- */

const TripForm = ({
  onTripGenerated,
  hasPlannedTrip,
  onViewPlannedTrip,
  user,
  authLoading,
  onOpenAuth,
  onLogout,
  onOpenMyTrips,
  onOpenFavorites,
}) => {
  const plannerRef = useRef(null);
  const currencyDropdownRef =
    useRef(null);
  const accountMenuRef =
    useRef(null);

  /*
   * HARD SUBMIT LOCK
   *
   * Prevents multiple /plan-trip requests when
   * the user clicks CREATE MY JOURNEY repeatedly
   * before React has updated loading state.
   */
  const submitLockRef = useRef(false);

  /*
   * Recommendation request lock.
   *
   * Prevents multiple recommendation requests
   * from rapid clicks.
   */
  const recommendationLockRef =
    useRef(false);

  const [
    currencyDropdownOpen,
    setCurrencyDropdownOpen,
  ] = useState(false);

  const [
    departureDate,
    setDepartureDate,
  ] = useState("");

  const [
    returnDate,
    setReturnDate,
  ] = useState("");

  const [formData, setFormData] =
    useState({
      destination: "",
      days: 0,
      budget: "",
      currency: "INR",
      restaurant_budget:
        "moderate",
      walking_preference: true,
      hotel_preference:
        "mid-range",
    });

  /*
   * Interests are intentionally kept separate
   * from formData.
   */
  const [
    selectedInterests,
    setSelectedInterests,
  ] = useState(
    INTERESTS.map(
      (interest) => interest.id
    ).filter(() => false)
  );

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  /* -------------------------------------------------------
     DAY 9 — ML RECOMMENDATIONS
  ------------------------------------------------------- */

  const [
    recommendations,
    setRecommendations,
  ] = useState([]);

  const [
    recommendationLoading,
    setRecommendationLoading,
  ] = useState(false);

  const [
    recommendationError,
    setRecommendationError,
  ] = useState("");

  const [
    accountMenuOpen,
    setAccountMenuOpen,
  ] = useState(false);

  const selectedCurrency =
    CURRENCY_OPTIONS.find(
      (currency) =>
        currency.code ===
        formData.currency
    ) ||
    CURRENCY_OPTIONS[0];

  /* -------------------------------------------------------
     ALWAYS START PAGE AT TOP
  ------------------------------------------------------- */

  useLayoutEffect(() => {
    const html =
      document.documentElement;

    const previousScrollBehavior =
      html.style.scrollBehavior;

    if (
      "scrollRestoration" in
      window.history
    ) {
      window.history.scrollRestoration =
        "manual";
    }

    html.style.scrollBehavior =
      "auto";

    const forceTop = () => {
      window.scrollTo(0, 0);
    };

    forceTop();

    const frame =
      requestAnimationFrame(
        forceTop
      );

    const timeout1 =
      setTimeout(forceTop, 50);

    const timeout2 =
      setTimeout(forceTop, 150);

    const timeout3 =
      setTimeout(forceTop, 400);

    const handlePageShow = () => {
      forceTop();
    };

    window.addEventListener(
      "pageshow",
      handlePageShow
    );

    return () => {
      cancelAnimationFrame(frame);

      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);

      window.removeEventListener(
        "pageshow",
        handlePageShow
      );

      html.style.scrollBehavior =
        previousScrollBehavior;

      if (
        "scrollRestoration" in
        window.history
      ) {
        window.history.scrollRestoration =
          "auto";
      }
    };
  }, []);

  /* -------------------------------------------------------
     CURRENCY DROPDOWN
  ------------------------------------------------------- */

  useEffect(() => {
    const handleClickOutside = (
      event
    ) => {
      if (
        currencyDropdownRef.current &&
        !currencyDropdownRef.current.contains(
          event.target
        )
      ) {
        setCurrencyDropdownOpen(
          false
        );
      }
    };

    const handleKeyDown = (
      event
    ) => {
      if (event.key === "Escape") {
        setCurrencyDropdownOpen(
          false
        );
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    document.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );

      document.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, []);

  /* -------------------------------------------------------
     ACCOUNT DROPDOWN
  ------------------------------------------------------- */

  useEffect(() => {
    const handleOutside = (
      event
    ) => {
      if (
        accountMenuRef.current &&
        !accountMenuRef.current.contains(
          event.target
        )
      ) {
        setAccountMenuOpen(false);
      }
    };

    const handleEscape = (
      event
    ) => {
      if (event.key === "Escape") {
        setAccountMenuOpen(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleOutside
    );

    document.addEventListener(
      "keydown",
      handleEscape
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutside
      );

      document.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, []);

  const displayName =
    user?.username ||
    user?.name ||
    user?.full_name ||
    user?.email?.split("@")[0] ||
    "ACCOUNT";

  const userInitial =
    displayName
      .trim()
      .charAt(0)
      .toUpperCase() || "V";

  /* -------------------------------------------------------
     BASIC INPUT HANDLER
  ------------------------------------------------------- */

  const handleChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setFormData(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );

    setError("");
    setRecommendationError("");

    setRecommendations([]);
  };

  /* -------------------------------------------------------
     DATE HANDLERS
  ------------------------------------------------------- */

  const handleDepartureChange = (
    event
  ) => {
    const nextDeparture =
      event.target.value;

    setDepartureDate(
      nextDeparture
    );

    setError("");
    setRecommendationError("");
    setRecommendations([]);

    if (
      returnDate &&
      nextDeparture >= returnDate
    ) {
      setReturnDate("");

      setFormData(
        (previous) => ({
          ...previous,
          days: 0,
        })
      );

      return;
    }

    if (returnDate) {
      const days =
        calculateTripDays(
          nextDeparture,
          returnDate
        );

      setFormData(
        (previous) => ({
          ...previous,
          days,
        })
      );
    }
  };

  const handleReturnChange = (
    event
  ) => {
    const nextReturn =
      event.target.value;

    setReturnDate(nextReturn);

    setError("");
    setRecommendationError("");
    setRecommendations([]);

    const days =
      calculateTripDays(
        departureDate,
        nextReturn
      );

    setFormData(
      (previous) => ({
        ...previous,
        days,
      })
    );
  };

  /* -------------------------------------------------------
     INTERESTS
  ------------------------------------------------------- */

  const toggleInterest = (
    interestId
  ) => {
    const normalizedId =
      String(interestId)
        .trim()
        .toLowerCase();

    setSelectedInterests(
      (previous) => {
        const current =
          new Set(
            Array.isArray(
              previous
            )
              ? previous
              : []
          );

        if (
          current.has(
            normalizedId
          )
        ) {
          current.delete(
            normalizedId
          );
        } else {
          current.add(
            normalizedId
          );
        }

        return INTERESTS
          .map(
            (interest) =>
              interest.id
          )
          .filter(
            (id) =>
              current.has(id)
          );
      }
    );

    setError("");
    setRecommendationError("");
    setRecommendations([]);
  };

  /* -------------------------------------------------------
     SCROLL TO PLANNER
  ------------------------------------------------------- */

  const scrollToPlanner = () => {
    plannerRef.current?.scrollIntoView(
      {
        behavior: "smooth",
        block: "start",
      }
    );
  };

  /* -------------------------------------------------------
     DAY 9 — GET ML RECOMMENDATIONS
  ------------------------------------------------------- */

  const handleGetRecommendations =
    async () => {
      /*
       * Prevent rapid duplicate requests.
       */
      if (
        recommendationLockRef.current ||
        recommendationLoading
      ) {
        return;
      }

      setRecommendationError("");
      setRecommendations([]);

      const tripDays =
        calculateTripDays(
          departureDate,
          returnDate
        );

      if (
        !departureDate ||
        !returnDate
      ) {
        setRecommendationError(
          "Please select your departure and return dates first."
        );
        return;
      }

      if (tripDays < 1) {
        setRecommendationError(
          "Return date must be after your departure date."
        );
        return;
      }

      if (
        !formData.budget ||
        Number(formData.budget) <= 0
      ) {
        setRecommendationError(
          "Please enter your total trip budget first."
        );
        return;
      }

      if (
        selectedInterests.length ===
        0
      ) {
        setRecommendationError(
          "Please select at least one interest first."
        );
        return;
      }

      const recommendationPayload =
        {
          interests:
            selectedInterests,

          budget:
            Number(
              formData.budget
            ),

          currency:
            formData.currency,

          days:
            Number(tripDays),

          walking_preference:
            formData.walking_preference,

          top_k: 5,
        };

      try {
        recommendationLockRef.current =
          true;

        setRecommendationLoading(
          true
        );

        console.log(
          "🤖 Requesting universal-currency AI recommendations..."
        );

        console.log(
          "📊 Recommendation payload:",
          recommendationPayload
        );

        const response =
          await API.post(
            "/recommendations",
            recommendationPayload
          );

        console.log(
          "✅ AI recommendations received:",
          response.data
        );

        if (
          response?.data
            ?.success &&
          Array.isArray(
            response.data
              .recommendations
          )
        ) {
          setRecommendations(
            response.data
              .recommendations
          );

          return;
        }

        setRecommendationError(
          response?.data
            ?.error ||
            "Unable to generate destination recommendations."
        );
      } catch (err) {
        console.error(
          "❌ Recommendation request failed:",
          err
        );

        setRecommendationError(
          err?.response
            ?.data?.detail ||
            err?.response
              ?.data?.error ||
            "Unable to load AI destination recommendations."
        );
      } finally {
        recommendationLockRef.current =
          false;

        setRecommendationLoading(
          false
        );
      }
    };

  /* -------------------------------------------------------
     SUBMIT
  ------------------------------------------------------- */

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    /*
     * HARD PROTECTION AGAINST
     * MULTIPLE /plan-trip REQUESTS
     *
     * React state updates are asynchronous.
     * Therefore loading alone is not enough to
     * protect against extremely fast repeated clicks.
     */
    if (
      submitLockRef.current ||
      loading
    ) {
      return;
    }

    setError("");

    const tripDays =
      calculateTripDays(
        departureDate,
        returnDate
      );

    if (
      !formData.destination.trim()
    ) {
      setError(
        "Please enter a destination."
      );
      return;
    }

    if (
      !departureDate ||
      !returnDate
    ) {
      setError(
        "Please select your departure and return dates."
      );
      return;
    }

    if (tripDays < 1) {
      setError(
        "Return date must be after your departure date."
      );
      return;
    }

    if (
      !formData.budget ||
      Number(formData.budget) <= 0
    ) {
      setError(
        "Please enter a valid trip budget."
      );
      return;
    }

    if (
      selectedInterests.length ===
      0
    ) {
      setError(
        "Please select at least one interest."
      );
      return;
    }

    /*
     * LOCK BEFORE THE API REQUEST.
     */
    submitLockRef.current =
      true;

    const payload = {
      destination:
        formData.destination.trim(),

      /*
       * DATES ARE ALREADY CORRECTLY
       * SENT TO THE BACKEND.
       */
      departure_date:
        departureDate,

      return_date:
        returnDate,

      days:
        Number(tripDays),

      budget:
        Number(formData.budget),

      currency:
        formData.currency,

      interests: [
        ...selectedInterests,
      ],

      preferences: {
        restaurant_budget:
          formData.restaurant_budget,

        walking_preference:
          formData.walking_preference,

        hotel_preference:
          formData.hotel_preference,
      },
    };

    console.log(
      "🔥 FINAL INTERESTS SENT TO BACKEND:",
      payload.interests
    );

    console.log(
      "🔥 FINAL INTEREST COUNT:",
      payload.interests.length
    );

    console.log(
      "🔥 FINAL DEPARTURE DATE:",
      payload.departure_date
    );

    console.log(
      "🔥 FINAL RETURN DATE:",
      payload.return_date
    );

    console.log(
      "🔥 FINAL TRIP DAYS:",
      payload.days
    );

    try {
      setLoading(true);

      console.log(
        "🚀 Creating VoyageMind journey..."
      );

      const response =
        await API.post(
          "/plan-trip",
          payload
        );

      console.log(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      );

      console.log(
        "🧪 VOYAGEMIND DEBUG RESPONSE"
      );

      console.log(
        "Trip interests:",
        response?.data?.trip
          ?.interests
      );

      console.log(
        "Trip interest count:",
        response?.data?.trip
          ?.interests?.length
      );

      console.log(
        "Trip departure date:",
        response?.data?.trip
          ?.departure_date
      );

      console.log(
        "Trip return date:",
        response?.data?.trip
          ?.return_date
      );

      console.log(
        "Places count:",
        response?.data?.places
          ?.count
      );

      console.log(
        "Actual places array length:",
        response?.data?.places
          ?.places?.length
      );

      console.log(
        "Category distribution:",
        response?.data?.places
          ?.category_distribution
      );

      console.log(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      );

      console.log(
        "✅ Journey generated successfully:",
        response.data
      );

      if (
        onTripGenerated &&
        response?.data?.success
      ) {
        onTripGenerated(
          response.data
        );
      }
    } catch (err) {
      console.error(
        "❌ Journey generation failed:",
        err
      );

      setError(
        err?.response
          ?.data?.detail ||
          err?.response
            ?.data?.error ||
          "Something went wrong while creating your journey."
      );
    } finally {
      /*
       * ALWAYS RELEASE THE LOCK.
       */
      submitLockRef.current =
        false;

      setLoading(false);
    }
  };

  const tripDays =
    calculateTripDays(
      departureDate,
      returnDate
    );

  return (
    <main className="voyage-page">

      {/* ---------------------------------------------------
          BACKGROUND
      --------------------------------------------------- */}

      <div className="voyage-bg">
        <div className="voyage-orb voyage-orb-one" />
        <div className="voyage-orb voyage-orb-two" />
        <div className="voyage-grid" />
      </div>

      {/* ---------------------------------------------------
          NAVBAR
      --------------------------------------------------- */}

      <nav className="voyage-nav voyage-container">

        <div className="voyage-brand">

          <div className="brand-mark">
            V
          </div>

          <div className="brand-text">
            <strong>
              VoyageMind
            </strong>

            <span>
              AI TRAVEL INTELLIGENCE
            </span>
          </div>

        </div>

        <div className="nav-right">

          {hasPlannedTrip && (
            <button
              type="button"
              className="nav-trip-button planned-trip-nav-button"
              onClick={
                onViewPlannedTrip
              }
            >
              <span>
                VIEW PLANNED JOURNEY
              </span>

              <span>
                →
              </span>
            </button>
          )}

          <button
            type="button"
            className="nav-trip-button"
            onClick={
              scrollToPlanner
            }
          >
            <span>
              PLAN A TRIP
            </span>

            <span>
              ↓
            </span>
          </button>

          <div className="online-status">
            <span className="online-dot" />
            ONLINE
          </div>

          <div
            className="voyagemind-account"
            ref={accountMenuRef}
          >

            {authLoading ? (
              <div
                className="voyagemind-account-loading"
                aria-label="Loading account"
              >
                <span />
              </div>
            ) : user ? (
              <>
                <button
                  type="button"
                  className="voyagemind-account-trigger"
                  onClick={() =>
                    setAccountMenuOpen(
                      (previous) =>
                        !previous
                    )
                  }
                  aria-expanded={
                    accountMenuOpen
                  }
                  aria-haspopup="menu"
                  aria-label="Open account menu"
                >
                  <span className="voyagemind-account-avatar">
                    {userInitial}
                  </span>

                  <span className="voyagemind-account-name">
                    {displayName}
                  </span>

                  <span
                    className={
                      accountMenuOpen
                        ? "voyagemind-account-chevron open"
                        : "voyagemind-account-chevron"
                    }
                  >
                    ↓
                  </span>
                </button>

                {accountMenuOpen && (
                  <div
                    className="voyagemind-account-menu"
                    role="menu"
                  >
                    <div className="voyagemind-account-header">

                      <div className="voyagemind-account-avatar large">
                        {userInitial}
                      </div>

                      <div className="voyagemind-account-details">
                        <strong>
                          {displayName}
                        </strong>

                        {user.email && (
                          <span>
                            {user.email}
                          </span>
                        )}
                      </div>

                    </div>

                    <div className="voyagemind-account-divider" />

                    <button
                      type="button"
                      className="voyagemind-account-item"
                      onClick={() => {
                        setAccountMenuOpen(
                          false
                        );

                        onOpenMyTrips?.();
                      }}
                    >
                      <span>
                        ◫
                      </span>

                      <span>
                        MY TRIPS
                      </span>
                    </button>

                    <button
                      type="button"
                      className="voyagemind-account-item"
                      onClick={() => {
                        setAccountMenuOpen(
                          false
                        );

                        onOpenFavorites?.();
                      }}
                    >
                      <span>
                        ♡
                      </span>

                      <span>
                        FAVORITES
                      </span>
                    </button>

                    <div className="voyagemind-account-divider" />

                    <button
                      type="button"
                      className="voyagemind-account-item logout"
                      onClick={() => {
                        setAccountMenuOpen(
                          false
                        );

                        onLogout?.();
                      }}
                    >
                      <span>
                        ↪
                      </span>

                      <span>
                        SIGN OUT
                      </span>
                    </button>

                  </div>
                )}
              </>
            ) : (
              <button
                type="button"
                className="voyagemind-signin-button"
                onClick={
                  onOpenAuth
                }
              >
                SIGN IN →
              </button>
            )}

          </div>

        </div>

      </nav>

      {/* ---------------------------------------------------
          HERO
      --------------------------------------------------- */}

      <section className="voyage-hero voyage-container">

        <div className="hero-copy">

          <div className="hero-eyebrow">
            <span />
            AUTONOMOUS TRAVEL PLANNING
          </div>

          <h1>
            Travel planning,
            <br />
            <span>
              reimagined.
            </span>
          </h1>

          <p className="hero-description">
            Tell VoyageMind where you want
            to go. Our AI builds the route,
            experiences, stays and moments
            around you.
          </p>

          <div className="hero-actions">

            <button
              type="button"
              className="primary-action"
              onClick={
                scrollToPlanner
              }
            >
              <span>
                START PLANNING
              </span>

              <span className="action-arrow">
                ↓
              </span>
            </button>

            <div className="hero-trust">
              <span>
                ✦
              </span>

              AI-POWERED

              <span className="trust-separator">
                •
              </span>

              PERSONALIZED
            </div>

          </div>

          {/* ------------------------------------------------
              PLANNED JOURNEY BANNER
          ------------------------------------------------ */}

          {hasPlannedTrip && (
            <div className="planned-journey-banner">

              <div className="planned-journey-info">

                <span className="planned-journey-status">
                  ● JOURNEY SAVED
                </span>

                <strong>
                  Your planned journey is ready.
                </strong>

                <small>
                  Continue exploring the itinerary
                  you already created.
                </small>

              </div>

              <button
                type="button"
                className="planned-journey-button"
                onClick={
                  onViewPlannedTrip
                }
              >
                <span>
                  VIEW JOURNEY
                </span>

                <span>
                  →
                </span>
              </button>

            </div>
          )}

          <div className="hero-features">

            <div className="hero-feature">

              <span>
                ✦
              </span>

              <div>
                <strong>
                  Smart itineraries
                </strong>

                <small>
                  Built around your interests
                </small>
              </div>

            </div>

            <div className="hero-feature">

              <span>
                ⌁
              </span>

              <div>
                <strong>
                  Local intelligence
                </strong>

                <small>
                  Places worth actually visiting
                </small>
              </div>

            </div>

            <div className="hero-feature">

              <span>
                ◌
              </span>

              <div>
                <strong>
                  Budget aware
                </strong>

                <small>
                  Plans that respect your budget
                </small>
              </div>

            </div>

          </div>

        </div>

        {/* ---------------------------------------------------
            HERO IMAGE
        --------------------------------------------------- */}

        <div className="hero-visual">

          <div className="hero-image-card">

            <img
              src={heroImage}
              alt="Travel destination"
            />

            <div className="hero-image-overlay" />

            <div className="image-location-card">

              <span className="location-pin">
                ✈️
              </span>

              <div>

                <small>
                  DISCOVER YOUR NEXT
                </small>

                <strong>
                  JOURNEY
                </strong>

              </div>

            </div>

            <div className="image-status-card">

              <span className="status-ring" />

              <div>

                <small>
                  TRAVEL ENGINE
                </small>

                <strong>
                  READY
                </strong>

              </div>

            </div>

          </div>

        </div>

      </section>

      {/* ---------------------------------------------------
          CAPABILITIES
      --------------------------------------------------- */}

      <section className="capabilities voyage-container">

        <div className="capability-item">
          <span>
            01
          </span>

          <strong>
            DESTINATION
          </strong>

          <small>
            Where to go
          </small>
        </div>

        <div className="capability-line" />

        <div className="capability-item">
          <span>
            02
          </span>

          <strong>
            PREFERENCES
          </strong>

          <small>
            What you love
          </small>
        </div>

        <div className="capability-line" />

        <div className="capability-item">
          <span>
            03
          </span>

          <strong>
            ITINERARY
          </strong>

          <small>
            Built by AI
          </small>
        </div>

      </section>

      {/* ---------------------------------------------------
          PLANNER
      --------------------------------------------------- */}

      <section
        ref={plannerRef}
        className="planner-section voyage-container"
      >

        <div className="planner-card">

          <div className="planner-header">

            <div>

              <span className="section-kicker">
                ✦ BUILD YOUR JOURNEY
              </span>

              <h2>
                Where would you like to go?
              </h2>

              <p>
                Tell us a little about your trip.
                VoyageMind will take care of the rest.
              </p>

            </div>

          </div>

          <form onSubmit={handleSubmit}>

            {/* ------------------------------------------------
                DESTINATION
            ------------------------------------------------ */}

            <div className="form-section destination-section">

              <div className="section-label-row">

                <label className="form-label">
                  <span>
                    ✦
                  </span>

                  DESTINATION
                </label>

                <span className="section-hint">
                  CITY / COUNTRY
                </span>

              </div>

              <div className="destination-box">

                <span className="destination-icon">
                  ◉
                </span>

                <input
                  type="text"
                  name="destination"
                  value={
                    formData.destination
                  }
                  onChange={
                    handleChange
                  }
                  placeholder="Paris, Tokyo, Dubai, Barcelona..."
                  autoComplete="off"
                />

                {formData.destination && (
                  <button
                    type="button"
                    className="clear-destination"
                    onClick={() =>
                      setFormData(
                        (previous) => ({
                          ...previous,
                          destination: "",
                        })
                      )
                    }
                  >
                    ×
                  </button>
                )}

              </div>

              <div className="destination-helper">
                ✦ Start with a city or country
              </div>

            </div>

            {/* ------------------------------------------------
                DATES
            ------------------------------------------------ */}

            <div className="form-section dates-section">

              <div className="section-label-row">

                <label className="form-label">
                  <span>
                    ◷
                  </span>

                  WHEN ARE YOU TRAVELLING?
                </label>

                {tripDays > 0 && (
                  <span className="duration-badge">
                    ✦ {tripDays} DAYS
                  </span>
                )}

              </div>

              <div className="date-range-grid">

                <div className="date-card">

                  <div className="date-card-top">

                    <span className="date-card-label">
                      DEPARTURE
                    </span>

                    <span className="date-card-icon">
                      ↗
                    </span>

                  </div>

                  <div className="date-input-wrap">

                    <span className="calendar-icon">
                      ▣
                    </span>

                    <input
                      type="date"
                      value={
                        departureDate
                      }
                      onChange={
                        handleDepartureChange
                      }
                      min={
                        new Date()
                          .toISOString()
                          .split("T")[0]
                      }
                    />

                  </div>

                  <div className="date-preview">
                    {formatDatePreview(
                      departureDate
                    )}
                  </div>

                </div>

                <div className="date-card">

                  <div className="date-card-top">

                    <span className="date-card-label">
                      RETURN
                    </span>

                    <span className="date-card-icon">
                      ↙
                    </span>

                  </div>

                  <div className="date-input-wrap">

                    <span className="calendar-icon">
                      ▣
                    </span>

                    <input
                      type="date"
                      value={
                        returnDate
                      }
                      onChange={
                        handleReturnChange
                      }
                      min={
                        departureDate ||
                        new Date()
                          .toISOString()
                          .split("T")[0]
                      }
                    />

                  </div>

                  <div className="date-preview">
                    {formatDatePreview(
                      returnDate
                    )}
                  </div>

                </div>

              </div>

              <div className="duration-summary">

                <div className="duration-main">

                  <span className="duration-icon">
                    ✦
                  </span>

                  <div>

                    <small>
                      TRIP DURATION
                    </small>

                    <strong>
                      {tripDays > 0
                        ? `${tripDays} days trip · ${tripDays} nights`
                        : "Select your dates"}
                    </strong>

                  </div>

                </div>

                <span className="duration-note">
                  Duration calculated automatically
                </span>

              </div>

            </div>

            {/* ------------------------------------------------
                BUDGET
            ------------------------------------------------ */}

            <div className="form-section budget-section">

              <div className="section-label-row">

                <label className="form-label">
                  <span>
                    ◈
                  </span>

                  TOTAL TRIP BUDGET
                </label>

                <span className="section-hint">
                  Flights + Stay + Experiences
                </span>

              </div>

              <div className="budget-box">

                <div
                  ref={
                    currencyDropdownRef
                  }
                  className={`currency-selector ${
                    currencyDropdownOpen
                      ? "currency-selector-open"
                      : ""
                  }`}
                >

                  <button
                    type="button"
                    className="currency-trigger"
                    onClick={() =>
                      setCurrencyDropdownOpen(
                        (previous) =>
                          !previous
                      )
                    }
                    aria-haspopup="listbox"
                    aria-expanded={
                      currencyDropdownOpen
                    }
                    aria-label={`Selected currency: ${selectedCurrency.code}, ${selectedCurrency.name}`}
                  >

                    <span className="currency-trigger-symbol">
                      {
                        selectedCurrency.symbol
                      }
                    </span>

                    <span className="currency-trigger-content">

                      <span className="currency-trigger-code">
                        {
                          selectedCurrency.code
                        }
                      </span>

                      <span className="currency-trigger-name">
                        {
                          selectedCurrency.name
                        }
                      </span>

                    </span>

                    <span
                      className={`currency-trigger-chevron ${
                        currencyDropdownOpen
                          ? "open"
                          : ""
                      }`}
                      aria-hidden="true"
                    >
                      ↓
                    </span>

                  </button>

                  {currencyDropdownOpen && (
                    <div
                      className="currency-dropdown"
                      role="listbox"
                      aria-label="Select currency"
                    >

                      <div className="currency-dropdown-heading">

                        <div>

                          <span className="currency-dropdown-title">
                            Currency
                          </span>

                          <span className="currency-dropdown-subtitle">
                            Choose your display currency
                          </span>

                        </div>

                        <span className="currency-dropdown-current">
                          {
                            selectedCurrency.code
                          }
                        </span>

                      </div>

                      <div className="currency-options">

                        {CURRENCY_OPTIONS.map(
                          (currency) => {
                            const selected =
                              formData.currency ===
                              currency.code;

                            return (
                              <button
                                key={
                                  currency.code
                                }
                                type="button"
                                role="option"
                                aria-selected={
                                  selected
                                }
                                className={`currency-option ${
                                  selected
                                    ? "currency-option-selected"
                                    : ""
                                }`}
                                onClick={() => {

                                  setFormData(
                                    (previous) => ({
                                      ...previous,
                                      currency:
                                        currency.code,
                                    })
                                  );

                                  setCurrencyDropdownOpen(
                                    false
                                  );

                                  setError("");

                                  setRecommendationError(
                                    ""
                                  );

                                  setRecommendations(
                                    []
                                  );
                                }}
                              >

                                <span className="currency-option-symbol">
                                  {
                                    currency.symbol
                                  }
                                </span>

                                <span className="currency-option-code">
                                  {
                                    currency.code
                                  }
                                </span>

                                <span className="currency-option-name">
                                  {
                                    currency.name
                                  }
                                </span>

                                <span
                                  className={`currency-option-check ${
                                    selected
                                      ? "visible"
                                      : ""
                                  }`}
                                  aria-hidden="true"
                                >
                                  ✓
                                </span>

                              </button>
                            );
                          }
                        )}

                      </div>

                    </div>
                  )}

                </div>

                <div className="budget-input-area">

                  <span className="currency-prefix">
                    {
                      selectedCurrency.symbol
                    }
                  </span>

                  <input
                    type="number"
                    name="budget"
                    value={
                      formData.budget
                    }
                    onChange={
                      handleChange
                    }
                    placeholder="100000"
                    min="1"
                  />

                </div>

                <span className="budget-total-label">
                  TOTAL
                </span>

              </div>

              <div className="budget-helper">
                Set the maximum amount you want to
                spend on this journey.
              </div>

            </div>

            {/* ------------------------------------------------
                INTERESTS
            ------------------------------------------------ */}

            <div className="form-section interests-section">

              <div className="section-label-row">

                <label className="form-label">
                  <span>
                    ✦
                  </span>

                  WHAT ARE YOU INTO?
                </label>

                <span className="selected-count">
                  {
                    selectedInterests.length
                  }{" "}
                  SELECTED
                </span>

              </div>

              <p className="interest-description">
                Select as many as you like. We'll shape
                your journey around them.
              </p>

              <div className="interest-grid">

                {INTERESTS.map(
                  (interest) => {
                    const selected =
                      selectedInterests.includes(
                        interest.id
                      );

                    return (
                      <button
                        key={
                          interest.id
                        }
                        type="button"
                        className={`interest-card ${
                          selected
                            ? "selected"
                            : ""
                        }`}
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();

                          toggleInterest(
                            interest.id
                          );
                        }}
                        aria-pressed={
                          selected
                        }
                      >

                        <span className="interest-icon">
                          {
                            interest.icon
                          }
                        </span>

                        <span className="interest-name">
                          {
                            interest.label
                          }
                        </span>

                        <span className="interest-check">
                          {
                            selected
                              ? "✓"
                              : ""
                          }
                        </span>

                      </button>
                    );
                  }
                )}

              </div>

            </div>

            {/* ------------------------------------------------
                PREFERENCES
            ------------------------------------------------ */}

            <div className="form-section preferences-section">

              <div className="section-label-row preference-heading">

                <label className="form-label">
                  <span>
                    ✦
                  </span>

                  TRAVEL PREFERENCES
                </label>

              </div>

              <div className="preferences-grid">

                <div className="preference-card">

                  <div className="preference-card-header">

                    <div className="preference-icon restaurant-icon">
                      🍽️
                    </div>

                    <div>

                      <span>
                        DINING
                      </span>

                      <strong>
                        Restaurant style
                      </strong>

                    </div>

                  </div>

                  <div className="custom-select-wrap">

                    <select
                      name="restaurant_budget"
                      value={
                        formData.restaurant_budget
                      }
                      onChange={
                        handleChange
                      }
                    >

                      <option value="budget">
                        Budget friendly
                      </option>

                      <option value="moderate">
                        Moderate
                      </option>

                      <option value="premium">
                        Premium
                      </option>

                    </select>

                    <span
                      className="custom-select-arrow"
                      aria-hidden="true"
                    >
                      ↓
                    </span>

                  </div>

                </div>

                <div className="preference-card">

                  <div className="preference-card-header">

                    <div className="preference-icon hotel-icon">
                      🏨
                    </div>

                    <div>

                      <span>
                        STAY
                      </span>

                      <strong>
                        Hotel preference
                      </strong>

                    </div>

                  </div>

                  <div className="custom-select-wrap">

                    <select
                      name="hotel_preference"
                      value={
                        formData.hotel_preference
                      }
                      onChange={
                        handleChange
                      }
                    >

                      <option value="budget">
                        Budget
                      </option>

                      <option value="mid-range">
                        Mid-range
                      </option>

                      <option value="luxury">
                        Luxury
                      </option>

                    </select>

                    <span
                      className="custom-select-arrow"
                      aria-hidden="true"
                    >
                      ↓
                    </span>

                  </div>

                </div>

              </div>

              <button
                type="button"
                className={`walking-card ${
                  formData.walking_preference
                    ? "walking-active"
                    : ""
                }`}
                onClick={() => {

                  setFormData(
                    (previous) => ({
                      ...previous,
                      walking_preference:
                        !previous.walking_preference,
                    })
                  );

                  setRecommendations(
                    []
                  );

                  setRecommendationError(
                    ""
                  );
                }}
              >

                <div className="walking-left">

                  <div className="walking-icon">
                    🚶
                  </div>

                  <div className="walking-content">

                    <span>
                      PACE
                    </span>

                    <strong>
                      Prefer walking?
                    </strong>

                    <small>
                      Prioritize walkable experiences
                      and compact routes.
                    </small>

                  </div>

                </div>

                <div
                  className={`walking-switch ${
                    formData.walking_preference
                      ? "active"
                      : ""
                  }`}
                >
                  <span />
                </div>

              </button>

            </div>

            {/* ------------------------------------------------
                DAY 9 — AI DESTINATION RECOMMENDATIONS
            ------------------------------------------------ */}

            <div className="ml-recommendation-section">

              <div className="ml-section-header">

                <div className="ml-section-heading">

                  <span className="section-kicker">

                    <span className="kicker-line" />

                    AI DESTINATION INTELLIGENCE

                  </span>

                  <h3>
                    Not sure where to go?
                  </h3>

                  <p>
                    Let VoyageMind's recommendation
                    engine discover destinations that
                    match your interests, budget,
                    and travel style.
                  </p>

                </div>

                <div className="ml-engine-status">

                  <span className="ml-status-dot" />

                  <span>
                    ML ENGINE
                  </span>

                  <strong>
                    READY
                  </strong>

                </div>

              </div>

              <div className="ml-action-panel">

                <div className="ml-action-content">

                  <div className="ml-action-icon">
                    ✦
                  </div>

                  <div>

                    <span className="ml-action-label">
                      PERSONALIZED DISCOVERY
                    </span>

                    <strong>
                      Find your best destination
                    </strong>

                    <p>
                      Personalized using your travel
                      preferences.
                    </p>

                  </div>

                </div>

                <button
                  type="button"
                  className="ml-recommend-button"
                  onClick={
                    handleGetRecommendations
                  }
                  disabled={
                    recommendationLoading
                  }
                >

                  <span>
                    {
                      recommendationLoading
                        ? "ANALYZING YOUR PROFILE..."
                        : "GET AI DESTINATION MATCHES"
                    }
                  </span>

                  <span className="ml-button-arrow">
                    →
                  </span>

                </button>

              </div>

              {recommendationError && (
                <div className="ml-error-state">

                  <div className="ml-error-icon">
                    !
                  </div>

                  <div>

                    <strong>
                      Recommendation engine unavailable
                    </strong>

                    <p>
                      {
                        recommendationError
                      }
                    </p>

                  </div>

                </div>
              )}

              {recommendations.length >
                0 && (
                <div className="ml-results">

                  <div className="ml-results-header">

                    <div>

                      <span className="ml-results-kicker">
                        ✦ PERSONALIZED FOR YOU
                      </span>

                      <h4>
                        Top destination matches
                      </h4>

                      <p>
                        Ranked by VoyageMind's
                        recommendation engine
                      </p>

                    </div>

                    <div className="ml-match-count">

                      <strong>
                        {
                          recommendations.length
                        }
                      </strong>

                      <span>
                        MATCHES
                      </span>

                    </div>

                  </div>

                  <div className="ml-recommendation-grid">

                    {recommendations.map(
                      (
                        recommendation,
                        index
                      ) => {

                        const matchPercentage =
                          Number(
                            recommendation.match_percentage ||
                              0
                          );

                        return (
                          <article
                            className={`ml-recommendation-card ${
                              index === 0
                                ? "ml-recommendation-card-best"
                                : ""
                            }`}
                            key={`${recommendation.destination}-${index}`}
                          >

                            <div className="ml-card-top">

                              <div className="ml-rank">
                                {String(
                                  index + 1
                                ).padStart(
                                  2,
                                  "0"
                                )}
                              </div>

                              {index ===
                                0 && (
                                <span className="ml-best-badge">
                                  BEST MATCH
                                </span>
                              )}

                            </div>

                            <div className="ml-destination-meta">

                              <span>
                                DESTINATION
                              </span>

                              <span className="ml-destination-pin">
                                ◉
                              </span>

                            </div>

                            <h5>
                              {
                                recommendation.destination
                              }
                            </h5>

                            <div className="ml-match-row">

                              <span>
                                DESTINATION MATCH
                              </span>

                              <strong>
                                {
                                  matchPercentage.toFixed(
                                    2
                                  )
                                }
                                %
                              </strong>

                            </div>

                            <div className="ml-progress-track">

                              <div
                                className="ml-progress-fill"
                                style={{
                                  width: `${Math.min(
                                    matchPercentage,
                                    100
                                  )}%`,
                                }}
                              />

                            </div>

                            <div className="ml-card-stats">

                              <div>

                                <span>
                                  DAILY COST
                                </span>

                                <strong>
                                  {formatCurrency(
                                    recommendation.average_daily_cost,
                                    recommendation.currency ||
                                      formData.currency
                                  )}
                                </strong>

                              </div>

                              <div>

                                <span>
                                  HOTEL
                                </span>

                                <strong>
                                  {formatCurrency(
                                    recommendation.hotel_price,
                                    recommendation.currency ||
                                      formData.currency
                                  )}
                                </strong>

                              </div>

                              <div>

                                <span>
                                  DINING
                                </span>

                                <strong>
                                  {formatCurrency(
                                    recommendation.restaurant_price,
                                    recommendation.currency ||
                                      formData.currency
                                  )}
                                </strong>

                              </div>

                            </div>

                            <div className="ml-card-footer">

                              <span>
                                ML SCORE
                              </span>

                              <strong>
                                {Number(
                                  recommendation.ml_score ||
                                    0
                                ).toFixed(
                                  3
                                )}
                              </strong>

                            </div>

                          </article>
                        );
                      }
                    )}

                  </div>

                  <div className="ml-results-note">

                    <span>
                      ✦
                    </span>

                    <p>
                      Recommendations are personalized
                      using your selected interests, daily
                      budget, and walking preference.
                    </p>

                  </div>

                </div>
              )}

            </div>

            {/* ------------------------------------------------
                TRIP SUMMARY
            ------------------------------------------------ */}

            <div className="trip-summary">

              <div className="summary-item">

                <span className="summary-icon">
                  ▣
                </span>

                <div>

                  <small>
                    DATES
                  </small>

                  <strong>
                    {departureDate &&
                    returnDate
                      ? `${formatDatePreview(
                          departureDate
                        )} — ${formatDatePreview(
                          returnDate
                        )}`
                      : "Dates not selected"}
                  </strong>

                </div>

              </div>

              <div className="summary-item">

                <span className="summary-icon">
                  ✦
                </span>

                <div>

                  <small>
                    INTERESTS
                  </small>

                  <strong>
                    {
                      selectedInterests.length
                    }{" "}
                    selected
                  </strong>

                </div>

              </div>

              <div className="summary-item">

                <span className="summary-icon">
                  ◌
                </span>

                <div>

                  <small>
                    PACE
                  </small>

                  <strong>
                    {
                      formData.walking_preference
                        ? "Walk-friendly"
                        : "Flexible"
                    }
                  </strong>

                </div>

              </div>

            </div>

            {/* ------------------------------------------------
                ERROR
            ------------------------------------------------ */}

            {error && (
              <div className="form-error">

                <span>
                  !
                </span>

                {error}

              </div>
            )}

            {/* ------------------------------------------------
                SUBMIT
            ------------------------------------------------ */}

            <button
              type="submit"
              className="create-journey-button"
              disabled={loading}
            >

              <span>
                {loading
                  ? "BUILDING YOUR JOURNEY..."
                  : "CREATE MY JOURNEY"}
              </span>

              <span className="create-arrow">
                →
              </span>

            </button>

            <div className="form-footer">

              <span>
                ✦ Your preferences remain private
              </span>

              <span>
                ✦ Powered by AI travel intelligence
              </span>

            </div>

          </form>

        </div>

      </section>

    </main>
  );
};

export default TripForm;