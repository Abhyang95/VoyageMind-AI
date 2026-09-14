import {
  useLayoutEffect,
  useMemo,
  useState,
} from "react";
import "./DestinationDashboard.css";

const CATEGORY_META = {
  Architecture: {
    icon: "🏛️",
    description:
      "Iconic buildings, landmarks & city design",
  },

  History: {
    icon: "🏺",
    description:
      "Historic places & cultural heritage",
  },

  Food: {
    icon: "🍽️",
    description:
      "Local food, restaurants & culinary spots",
  },

  Nightlife: {
    icon: "🌙",
    description:
      "Bars, evening experiences & night spots",
  },

  Museums: {
    icon: "🖼️",
    description:
      "Museums, galleries & cultural experiences",
  },

  Nature: {
    icon: "🌿",
    description:
      "Parks, gardens & natural escapes",
  },

  Shopping: {
    icon: "🛍️",
    description:
      "Markets, stores & shopping districts",
  },

  Adventure: {
    icon: "🧗",
    description:
      "Outdoor activities & adventures",
  },
};

const CATEGORY_MAP = {
  architecture: "Architecture",
  history: "History",
  food: "Food",
  nightlife: "Nightlife",
  nature: "Nature",
  museum: "Museums",
  museums: "Museums",
  shopping: "Shopping",
  adventure: "Adventure",
};

function formatInterest(value) {
  if (!value) return "Other";

  const normalized = String(value)
    .trim()
    .toLowerCase();

  return (
    CATEGORY_MAP[normalized] ||
    String(value)
      .trim()
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

/*
 * ============================================================
 * GET ALL INTERESTS ASSOCIATED WITH A PLACE
 * ============================================================
 *
 * The backend can now return:
 *
 * interest: "Architecture"
 * interest_tags: ["Architecture", "History"]
 *
 * So the same physical place can correctly appear under
 * both Architecture and History.
 *
 * If interest_tags doesn't exist, we fall back to the
 * original interest fields so older API responses still work.
 */
function getPlaceInterests(place) {
  const interests = [];

  if (Array.isArray(place?.interest_tags)) {
    place.interest_tags.forEach((interest) => {
      const formatted = formatInterest(interest);

      if (
        formatted &&
        formatted !== "Other" &&
        !interests.includes(formatted)
      ) {
        interests.push(formatted);
      }
    });
  }

  const fallbackInterest =
    place?.interest ||
    place?.interest_category ||
    place?.interestCategory;

  if (fallbackInterest) {
    const formatted = formatInterest(fallbackInterest);

    if (
      formatted &&
      formatted !== "Other" &&
      !interests.includes(formatted)
    ) {
      interests.push(formatted);
    }
  }

  /*
   * If somehow no interest exists, keep the old
   * "Other" behaviour.
   */
  if (interests.length === 0) {
    interests.push("Other");
  }

  return interests;
}


function openGoogleMaps(place, destinationName) {
  const query = [
    place?.name,
    place?.address,
    destinationName,
  ]
    .filter(Boolean)
    .join(", ");

  if (!query) return;

  window.open(
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
      query
    )}`,
    "_blank",
    "noopener,noreferrer"
  );
}

function formatWeather(weather) {
  if (!weather) return null;

  const current = weather.current || weather;

  return {
    temperature:
      current.temperature ??
      current.temperature_2m ??
      current.temp ??
      "--",

    feelsLike:
      current.apparent_temperature ??
      current.feels_like ??
      current.feelsLike ??
      "--",

    condition:
      current.condition ??
      current.weather_description ??
      current.description ??
      "Current conditions",

    wind:
      current.wind_speed ??
      current.wind_speed_10m ??
      current.windSpeed ??
      "--",

    humidity:
      current.humidity ??
      current.relative_humidity_2m ??
      "--",

    icon:
      current.icon ??
      current.weather_icon ??
      "🌤️",
  };
}

function DestinationDashboard({ result, onBack }) {
  /*
   * ============================================================
   * REFRESH PAGE -> ALWAYS START FROM THE TOP
   * ============================================================
   */
  useLayoutEffect(() => {
    const html = document.documentElement;
    const body = document.body;

    const previousScrollRestoration =
      window.history.scrollRestoration;

    const previousScrollBehavior =
      html.style.scrollBehavior;

    /*
     * Prevent the browser from restoring the old scroll
     * position.
     */
    if ("scrollRestoration" in window.history) {
      window.history.scrollRestoration = "manual";
    }

    /*
     * Disable smooth scrolling while forcing the page
     * to the top.
     */
    html.style.scrollBehavior = "auto";

    const forceTop = () => {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: "auto",
      });

      html.scrollTop = 0;
      body.scrollTop = 0;
    };

    /*
     * Immediately move to the top.
     */
    forceTop();

    /*
     * Force again after React/browser rendering.
     */
    const frame1 = requestAnimationFrame(() => {
      forceTop();

      requestAnimationFrame(() => {
        forceTop();
      });
    });

    /*
     * Handle delayed content and browser restoration.
     */
    const timeout1 = window.setTimeout(
      forceTop,
      50
    );

    const timeout2 = window.setTimeout(
      forceTop,
      150
    );

    const timeout3 = window.setTimeout(
      forceTop,
      400
    );

    /*
     * Important for browser back-forward cache / pageshow.
     */
    const handlePageShow = () => {
      forceTop();
    };

    window.addEventListener(
      "pageshow",
      handlePageShow
    );

    return () => {
      cancelAnimationFrame(frame1);

      clearTimeout(timeout1);
      clearTimeout(timeout2);
      clearTimeout(timeout3);

      window.removeEventListener(
        "pageshow",
        handlePageShow
      );

      html.style.scrollBehavior =
        previousScrollBehavior;

      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration =
          previousScrollRestoration;
      }
    };
  }, []);

  const [
    expandedCategories,
    setExpandedCategories,
  ] = useState({});

  const destination = result?.destination || {};

  const weather = formatWeather(result?.weather);


 const rawPlaces = useMemo(() => {
  const placesData = result?.places;

  if (Array.isArray(placesData)) {
    return placesData;
  }

  return placesData?.places || [];
}, [result?.places]);

  const itineraryData = result?.itinerary || {};
  
  const distanceData = result?.distance || {};
  const itinerary =
    itineraryData.itinerary || itineraryData;

  const days = Array.isArray(itinerary?.days)
    ? itinerary.days
    : [];

  const trip = result?.trip || {};

  const coordinates = {
    latitude:
      destination.latitude ??
      destination.lat ??
      destination.coordinates?.latitude ??
      destination.coordinates?.lat,

    longitude:
      destination.longitude ??
      destination.lon ??
      destination.lng ??
      destination.coordinates?.longitude ??
      destination.coordinates?.lon,
  };

  const destinationName =
    destination.name ||
    destination.city ||
    trip.destination ||
    "Your Destination";

  const destinationDisplay = destinationName
    .replace(/\s+/g, " ")
    .trim();

  const country =
    destination.country ||
    destination.address?.country ||
    "";

  /*
   * ============================================================
   * GROUP PLACES BY ALL THEIR INTEREST TAGS
   * ============================================================
   *
   * OLD:
   *
   * place -> one category
   *
   * NEW:
   *
   * place -> multiple categories when applicable
   *
   * Example:
   *
   * Louvre
   *   -> Museums
   *   -> History
   *   -> Architecture
   *
   * This fixes the missing History category.
   */
  const groupedPlaces = useMemo(() => {
    const groups = {};

    rawPlaces.forEach((place) => {
      const interests =
        getPlaceInterests(place);

      interests.forEach((category) => {
        if (!groups[category]) {
          groups[category] = [];
        }

        /*
         * Prevent the exact same place from being added
         * twice to the same category.
         */
        const alreadyExists = groups[
          category
        ].some((existingPlace) => {
          const existingKey = [
            existingPlace?.name,
            existingPlace?.latitude ??
              existingPlace?.lat,
            existingPlace?.longitude ??
              existingPlace?.lon ??
              existingPlace?.lng,
          ]
            .filter(Boolean)
            .join("|");

          const currentKey = [
            place?.name,
            place?.latitude ??
              place?.lat,
            place?.longitude ??
              place?.lon ??
              place?.lng,
          ]
            .filter(Boolean)
            .join("|");

          return (
            existingKey === currentKey
          );
        });

        if (!alreadyExists) {
          groups[category].push(place);
        }
      });
    });

    return groups;
  }, [rawPlaces]);

  /*
   * ============================================================
   * CATEGORY ORDER
   * ============================================================
   *
   * Keep the order selected by the user.
   *
   * Backend:
   * museums
   * architecture
   * history
   * nature
   * food
   * shopping
   * nightlife
   * adventure
   *
   * Frontend will now follow the same order.
   */
  const categories = useMemo(() => {
    const selectedCategories =
      Array.isArray(trip.interests)
        ? trip.interests.map(formatInterest)
        : [];

    const existingCategories =
      Object.keys(groupedPlaces);

    const ordered = [];

    /*
     * First add categories selected by user.
     */
    selectedCategories.forEach(
      (category) => {
        if (
          groupedPlaces[category] &&
          !ordered.includes(category)
        ) {
          ordered.push(category);
        }
      }
    );

    /*
     * Then add any additional categories that
     * may have come from the API.
     */
    existingCategories.forEach(
      (category) => {
        if (!ordered.includes(category)) {
          ordered.push(category);
        }
      }
    );

    return ordered;
  }, [groupedPlaces, trip.interests]);

  const totalPlaces = rawPlaces.length;

  const totalActivities = days.reduce(
    (total, day) =>
      total +
      (Array.isArray(day.activities)
        ? day.activities.length
        : 0),
    0
  );

  const budget =
    itinerary?.budget_plan?.total_budget ??
    trip.budget ??
    "--";

  const currency =
    itinerary?.budget_plan?.currency ||
    trip.currency ||
    "INR";

  const duration =
    itinerary?.trip_summary?.duration_days ??
    trip.days ??
    days.length ??
    "--";

  const getVisiblePlaces = (category) => {
    return expandedCategories[category]
      ? groupedPlaces[category] || []
      : (groupedPlaces[category] || []).slice(
          0,
          6
        );
  };

  const toggleCategory = (category) => {
    setExpandedCategories((previous) => ({
      ...previous,
      [category]: !previous[category],
    }));
  };

  return (
    <main className="destination-dashboard">
      {/* ======================================================
          NAVIGATION
          ====================================================== */}

      <nav className="dashboard-nav">
        <div className="dashboard-container dashboard-nav-inner">
          <button
            className="back-button"
            onClick={onBack}
          >
            <span>←</span>
            <span>Back to Home</span>
          </button>

          <div className="dashboard-brand">
            <div className="dashboard-brand-mark">
              ✦
            </div>

            <div>
              <strong>VoyageMind</strong>
              <span>
                AI TRAVEL INTELLIGENCE
              </span>
            </div>
          </div>

          <div className="dashboard-live">
            <span />
            JOURNEY READY
          </div>
        </div>
      </nav>

      <div className="dashboard-container">
        {/* ======================================================
            DESTINATION HERO
            ====================================================== */}

        <section className="destination-hero">
          <div className="destination-hero-background" />

          <div className="destination-hero-content">
            <div className="destination-breadcrumb">
              <span>VOYAGEMIND</span>
              <i>/</i>
              <span>YOUR JOURNEY</span>
            </div>

            <div className="destination-title-row">
              <div>
                <div className="destination-eyebrow">
                  <span>✦</span>
                  YOUR PERSONALIZED ESCAPE
                </div>

                <h1>{destinationDisplay}</h1>

                {country && (
                  <div className="destination-country">
                    {country}
                  </div>
                )}

                <p>
                  Your AI-powered travel
                  intelligence is ready. Explore
                  verified places, live conditions
                  and a personalized itinerary
                  built around you.
                </p>
              </div>

              <div className="destination-ready">
                <div className="ready-icon">
                  ✓
                </div>

                <div>
                  <span>AI JOURNEY</span>
                  <strong>READY</strong>
                </div>
              </div>
            </div>

            <div className="hero-stats">
              <div className="hero-stat">
                <span>◷</span>

                <div>
                  <small>DURATION</small>

                  <strong>
                    {duration}{" "}
                    {duration === 1
                      ? "day"
                      : "days"}
                  </strong>
                </div>
              </div>

              <div className="hero-stat">
                <span>✦</span>

                <div>
                  <small>PLACES FOUND</small>
                  <strong>{totalPlaces}</strong>
                </div>
              </div>

              <div className="hero-stat">
                <span>◎</span>

                <div>
                  <small>AI ACTIVITIES</small>
                  <strong>
                    {totalActivities}
                  </strong>
                </div>
              </div>

              <div className="hero-stat">
                <span>◈</span>

                <div>
                  <small>TRAVEL STYLE</small>

                  <strong>
                    {itinerary?.trip_summary
                      ?.travel_style ||
                      "Personalized"}
                  </strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ======================================================
            OVERVIEW
            ====================================================== */}

        <section className="overview-grid">
          <article className="overview-card weather-card">
            <div className="card-topline">
              <span>LIVE CONDITIONS</span>
              <span className="card-dot" />
            </div>

            {weather ? (
              <>
                <div className="weather-main">
                  <div className="weather-icon">
                    {weather.icon}
                  </div>

                  <div>
                    <strong>
                      {weather.temperature}
                      {typeof weather.temperature ===
                      "number"
                        ? "°"
                        : ""}
                    </strong>

                    <span>
                      {weather.condition}
                    </span>
                  </div>
                </div>

                <div className="weather-details">
                  <div>
                    <small>FEELS LIKE</small>

                    <strong>
                      {weather.feelsLike}
                      {weather.feelsLike !==
                      "--"
                        ? "°"
                        : ""}
                    </strong>
                  </div>

                  <div>
                    <small>WIND</small>

                    <strong>
                      {weather.wind}
                      {weather.wind !== "--"
                        ? " km/h"
                        : ""}
                    </strong>
                  </div>

                  <div>
                    <small>HUMIDITY</small>

                    <strong>
                      {weather.humidity}
                      {weather.humidity !==
                      "--"
                        ? "%"
                        : ""}
                    </strong>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-card">
                Weather data unavailable.
              </div>
            )}
          </article>

          <article className="overview-card budget-card">
            <div className="card-topline">
              <span>TRIP BUDGET</span>
              <span>◈</span>
            </div>

            <div className="budget-main">
              <small>PLANNED SPEND</small>

              <strong>
                {currency}{" "}
                {typeof budget === "number"
                  ? budget.toLocaleString()
                  : budget}
              </strong>

              <span>
                {itinerary?.budget_plan
                  ?.estimated_daily_budget
                  ? `${currency} ${Number(
                      itinerary.budget_plan
                        .estimated_daily_budget
                    ).toLocaleString()} / day`
                  : "Personalized around your selected budget"}
              </span>
            </div>

            <div className="budget-line">
              <div />
            </div>

            <p>
              {itinerary?.budget_plan?.notes ||
                "Your itinerary has been planned around your selected budget."}
            </p>
          </article>

          <article className="overview-card location-card">
            <div className="card-topline">
              <span>DESTINATION</span>
              <span>⌖</span>
            </div>

            <div className="location-main">
              <div className="location-pin">
                ⌖
              </div>

              <div>
                <strong>
                  {destinationDisplay}
                </strong>

                <span>
                  {coordinates.latitude !=
                    null &&
                  coordinates.longitude !=
                    null
                    ? `${Number(
                        coordinates.latitude
                      ).toFixed(4)}°, ${Number(
                        coordinates.longitude
                      ).toFixed(4)}°`
                    : "Location verified"}
                </span>
              </div>
            </div>

            <button
              className="map-button"
              onClick={() =>
                openGoogleMaps(
                  {
                    name: destinationDisplay,
                  },
                  destinationDisplay
                )
              }
            >
              <span>
                Explore on Google Maps
              </span>
              <span>↗</span>
            </button>
          </article>
        </section><br/>

<article className="overview-card distance-card">
  <div className="card-topline">
    <span>TRAVEL DISTANCE</span>
    <span>🚶</span>
  </div>

  <div className="distance-main">
    <small>TOTAL JOURNEY DISTANCE</small>

    <strong>
      {distanceData?.success &&
      distanceData?.total_distance
        ? distanceData.total_distance
        : "--"}
    </strong>

    <span>
      {distanceData?.success &&
      distanceData?.total_travel_time
        ? `${distanceData.total_travel_time} ${
            distanceData.mode === "walk"
              ? "walking"
              : "travel"
          }`
        : "Route information unavailable"}
    </span>
  </div>

  {distanceData?.success &&
    distanceData?.route_count != null && (
      <div className="distance-route-summary">
        <span>
          {distanceData.route_count} route
          {distanceData.route_count !== 1
            ? "s"
            : ""}{" "}
          calculated
        </span>
      </div>
    )}
</article>
        {/* ======================================================
            AI SUMMARY
            ====================================================== */}

        {itinerary?.trip_summary && (
          <section className="ai-summary-section">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  ✦ VOYAGEMIND AI
                </span>

                <h2>
                  Your journey, understood.
                </h2>

                <p>
                  A clear overview of what your
                  trip is designed to feel like.
                </p>
              </div>

              <div className="ai-badge">
                <span>✦</span>
                AI GENERATED
              </div>
            </div>

            <div className="ai-summary-card">
              <div className="summary-quote">
                <span>“</span>

                <p>
                  {itinerary.trip_summary
                    .weather_summary ||
                    `A personalized ${duration}-day experience in ${destinationDisplay}.`}
                </p>

                <span className="quote-end">
                  ”
                </span>
              </div>

              <div className="summary-meta">
                <div>
                  <small>STYLE</small>

                  <strong>
                    {itinerary.trip_summary
                      .travel_style ||
                      "Personalized"}
                  </strong>
                </div>

                <div>
                  <small>INTERESTS</small>

                  <strong>
                    {Array.isArray(
                      trip.interests
                    )
                      ? trip.interests
                          .map(formatInterest)
                          .join(" · ")
                      : "Curated for you"}
                  </strong>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ======================================================
            AI ITINERARY
            ====================================================== */}

        {days.length > 0 && (
          <section className="itinerary-section">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  ✦ YOUR AI ITINERARY
                </span>

                <h2>
                  Days worth remembering.
                </h2>

                <p>
                  Your schedule is organized
                  around time, places, interests
                  and practical pacing.
                </p>
              </div>

              <div className="itinerary-count">
                {days.length} DAYS
              </div>
            </div>

            <div className="itinerary-timeline">
              {days.map((day, index) => (
                <article
                  className="day-card"
                  key={`day-${day.day || index}`}
                >
                  <div className="day-number">
                    <span>DAY</span>

                    <strong>
                      {String(
                        day.day || index + 1
                      ).padStart(2, "0")}
                    </strong>
                  </div>

                  <div className="day-content">
                    <div className="day-header">
                      <div>
                        <span className="day-label">
                          {day.theme ||
                            "Explore & Discover"}
                        </span>

                        <h3>
                          Day{" "}
                          {day.day || index + 1}
                        </h3>
                      </div>

                      <span className="activity-count">
                        {Array.isArray(
                          day.activities
                        )
                          ? `${day.activities.length} ${
                              day.activities
                                .length === 1
                                ? "experience"
                                : "experiences"
                            }`
                          : "Curated day"}
                      </span>
                    </div>

                    <div className="activities-list">
                      {Array.isArray(
                        day.activities
                      ) &&
                        day.activities.map(
                          (
                            activity,
                            activityIndex
                          ) => (
                            <div
                              className="activity-row"
                              key={`${activity.place}-${activityIndex}`}
                            >
                              <div className="activity-time">
                                {activity.time ||
                                  "Anytime"}
                              </div>

                              <div className="activity-line">
                                <span />
                              </div>

                              <div className="activity-info">
                                <div className="activity-title">
                                  <strong>
                                    {activity.place ||
                                      "Explore"}
                                  </strong>

                                  {activity.category && (
                                    <span>
                                      {formatInterest(
                                        activity.category
                                      )}
                                    </span>
                                  )}
                                </div>

                                {activity.reason && (
                                  <p>
                                    {
                                      activity.reason
                                    }
                                  </p>
                                )}

                                {activity.notes && (
                                  <small>
                                    {
                                      activity.notes
                                    }
                                  </small>
                                )}
                              </div>

                              {activity.estimated_cost && (
                                <div className="activity-cost">
                                  {
                                    activity.estimated_cost
                                  }
                                </div>
                              )}
                            </div>
                          )
                        )}
                    </div>

                    {day.daily_tip && (
                      <div className="daily-tip">
                        <span>✦</span>

                        <p>
                          {day.daily_tip}
                        </p>
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* ======================================================
            PLACES
            ====================================================== */}

        <section className="places-section">
          <div className="section-heading places-heading">
            <div className="places-heading-copy">
              <span className="section-kicker">
                ✦ DISCOVER YOUR DESTINATION
              </span>

              <h2>
                Places Curated for Your Trip
              </h2>

              <p>
                Verified locations organized
                around the interests you selected
                for this journey.
              </p>
            </div>

            <div className="places-total">
              <strong>{totalPlaces}</strong>
              <span>CURATED PLACES</span>
            </div>
          </div>

          {categories.length === 0 ? (
            <div className="no-places">
              <div className="no-places-icon">
                ⌖
              </div>

              <h3>
                No places were found.
              </h3>

              <p>
                Try planning another destination
                with different interests.
              </p>
            </div>
          ) : (
            <div className="category-list">
              {categories.map((category) => {
                const meta =
                  CATEGORY_META[category] || {
                    icon: "📍",
                    description:
                      "Interesting places worth discovering",
                  };

                const places =
                  groupedPlaces[category] || [];

                const visible =
                  getVisiblePlaces(category);

                const expanded =
                  !!expandedCategories[category];

                return (
                  <section
                    className="place-category"
                    key={category}
                  >
                    <div className="category-header">
                      <div className="category-heading-content">
                        <div className="category-icon">
                          {meta.icon}
                        </div>

                        <div>
                          <div className="category-name-row">
                            <h3>{category}</h3>

                            <span className="category-count">
                              {places.length}{" "}
                              {places.length === 1
                                ? "PLACE"
                                : "PLACES"}
                            </span>
                          </div>

                          <p>
                            {meta.description}
                          </p>
                        </div>
                      </div>

                      <div className="category-line" />
                    </div>

                    <div className="places-grid">
                      {visible.map(
                        (place, placeIndex) => (
                          <article
                            className="place-card"
                            key={`${category}-${place.name}-${placeIndex}`}
                          >
                            <div className="place-visual">
                              <div className="place-visual-icon">
                                {meta.icon}
                              </div>

                              <div className="place-visual-copy">
                                <span>
                                  {String(
                                    placeIndex + 1
                                  ).padStart(
                                    2,
                                    "0"
                                  )}
                                </span>

                                <small>
                                  {category.toUpperCase()}
                                </small>
                              </div>
                            </div>

                            <div className="place-content">
                              <div className="place-content-top">
                                <div className="place-name-block">
                                  <h4>
                                    {place.name ||
                                      "Unnamed place"}
                                  </h4>

                                  <span className="place-subcategory">
                                    {category}
                                  </span>
                                </div>

                                <span className="place-pin-small">
                                  ⌖
                                </span>
                              </div>

                              {(place.address ||
                                place.street ||
                                place.city) && (
                                <p className="place-address">
                                  {place.address ||
                                    [
                                      place.street,
                                      place.city,
                                    ]
                                      .filter(Boolean)
                                      .join(
                                        ", "
                                      )}
                                </p>
                              )}

                              {place.opening_hours && (
                                <div className="place-hours">
                                  <span>◷</span>
                                  <span>
                                    {
                                      place.opening_hours
                                    }
                                  </span>
                                </div>
                              )}

                              {(place.rating !=
                                null ||
                                place.review_count !=
                                  null) && (
                                <div className="place-rating">
                                  <span>★</span>

                                  {place.rating !=
                                    null && (
                                    <strong>
                                      {
                                        place.rating
                                      }
                                    </strong>
                                  )}

                                  {place.review_count !=
                                    null && (
                                    <small>
                                      {Number(
                                        place.review_count
                                      ).toLocaleString()}{" "}
                                      reviews
                                    </small>
                                  )}
                                </div>
                              )}

                              <button
                                className="place-map-button"
                                onClick={() =>
                                  openGoogleMaps(
                                    place,
                                    destinationDisplay
                                  )
                                }
                              >
                                <span>
                                  View on Google Maps
                                </span>

                                <span className="place-map-arrow">
                                  ↗
                                </span>
                              </button>
                            </div>
                          </article>
                        )
                      )}
                    </div>

                    {places.length > 6 && (
                      <button
                        className="show-more-button"
                        onClick={() =>
                          toggleCategory(
                            category
                          )
                        }
                      >
                        <span>
                          {expanded
                            ? "Show fewer places"
                            : `Show ${
                                places.length - 6
                              } more places`}
                        </span>

                        <span
                          className={
                            expanded
                              ? "rotate"
                              : ""
                          }
                        >
                          ↓
                        </span>
                      </button>
                    )}
                  </section>
                );
              })}
            </div>
          )}
        </section>

        {/* ======================================================
            TRAVEL TIPS
            ====================================================== */}

        {Array.isArray(
          itinerary?.travel_tips
        ) &&
          itinerary.travel_tips.length > 0 && (
            <section className="tips-section">
              <div className="section-heading">
                <div>
                  <span className="section-kicker">
                    ✦ SMART TRAVEL
                  </span>

                  <h2>
                    Travel smarter, not harder.
                  </h2>

                  <p>
                    Practical guidance generated
                    for this specific journey.
                  </p>
                </div>
              </div>

              <div className="tips-grid">
                {itinerary.travel_tips.map(
                  (tip, index) => (
                    <div
                      className="tip-card"
                      key={index}
                    >
                      <span>
                        {String(
                          index + 1
                        ).padStart(2, "0")}
                      </span>

                      <p>{tip}</p>
                    </div>
                  )
                )}
              </div>
            </section>
          )}

        {/* ======================================================
            WARNINGS
            ====================================================== */}

        {Array.isArray(
          itinerary?.warnings
        ) &&
          itinerary.warnings.length > 0 && (
            <section className="warnings-section">
              <div className="warning-header">
                <div className="warning-icon">
                  !
                </div>

                <div>
                  <span>TRAVEL NOTES</span>

                  <h3>
                    Keep these in mind
                  </h3>
                </div>
              </div>

              <div className="warnings-list">
                {itinerary.warnings.map(
                  (warning, index) => (
                    <div key={index}>
                      <span>•</span>
                      <p>{warning}</p>
                    </div>
                  )
                )}
              </div>
            </section>
          )}

        {/* ======================================================
            FOOTER
            ====================================================== */}

        <footer className="dashboard-footer">
          <div>
            <div className="footer-brand">
              <span>✦</span>
              VoyageMind
            </div>

            <p>
              Intelligent travel planning,
              built around you.
            </p>
          </div>

          <div className="footer-right">
            <span>
              AI GENERATED JOURNEY
            </span>

            <strong>✦</strong>
          </div>
        </footer>
      </div>
    </main>
  );
}

export default DestinationDashboard;