import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import "./DestinationDashboard.css";

const CATEGORY_META = {
  Architecture: {
    icon: "🕌",
    description: "Iconic buildings, landmarks & city design",
  },
  History: {
    icon: "🏺",
    description: "Historic places & cultural heritage",
  },
  Food: {
    icon: "🍜",
    description: "Local food, restaurants & culinary spots",
  },
  Nightlife: {
    icon: "🌃",
    description: "Bars, evening experiences & night spots",
  },
  Museums: {
    icon: "🏛️",
    description: "Museums, galleries & cultural experiences",
  },
  Nature: {
    icon: "🌿",
    description: "Parks, gardens & natural escapes",
  },
  Shopping: {
    icon: "🛒",
    description: "Markets, stores & shopping districts",
  },
  Adventure: {
    icon: "🏄",
    description: "Outdoor activities & adventures",
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

const WIKIMEDIA_API =
  "https://commons.wikimedia.org/w/api.php";

function formatInterest(value) {
  if (!value) return "Other";

  const normalized = String(value).trim().toLowerCase();

  return (
    CATEGORY_MAP[normalized] ||
    String(value)
      .trim()
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase()
      )
  );
}

function getCategoryMeta(category) {
  return (
    CATEGORY_META[category] || {
      icon: "📍",
      description: "Interesting places worth discovering",
    }
  );
}

async function searchWikimediaImage(searchText) {
  try {
    const params = new URLSearchParams({
      action: "query",
      generator: "search",
      gsrsearch: searchText,
      gsrnamespace: "6",
      gsrlimit: "5",
      prop: "imageinfo",
      iiprop: "url|descriptionurl",
      iiurlwidth: "1000",
      format: "json",
      origin: "*",
    });

    const response = await fetch(
      `${WIKIMEDIA_API}?${params.toString()}`
    );

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    const pages = Object.values(
      data?.query?.pages || {}
    );

    const page = pages.find(
      (item) =>
        item?.imageinfo?.[0]?.thumburl ||
        item?.imageinfo?.[0]?.url
    );

    if (!page) {
      return null;
    }

    const info = page.imageinfo[0];

    return {
      url: info.thumburl || info.url,
      sourceUrl: info.descriptionurl || null,
    };
  } catch {
    return null;
  }
}

function openGoogleMaps(place, destinationName) {
  if (!place) return;

  const query = [
    place?.name,
    place?.address,
    place?.street,
    place?.city,
    destinationName,
  ]
    .filter(Boolean)
    .join(", ");

  if (!query) return;

  const url =
    "https://www.google.com/maps/search/?api=1&query=" +
    encodeURIComponent(query);

  window.open(
    url,
    "_blank",
    "noopener,noreferrer"
  );
}

function formatWeather(weather) {
  if (!weather) {
    return null;
  }

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

function DestinationDashboard({
  result,
  onBack,
  onSaveJourney,
  journeySaved,
  journeySaving,
  onToggleFavorite,
  favoriteSaving,
  isFavorite,
}) {
  const [expandedCategories, setExpandedCategories] =
    useState({});

  const [heroImage, setHeroImage] =
    useState(null);

useLayoutEffect(() => {
  window.history.scrollRestoration = "manual";

  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "auto",
  });

  return () => {
    window.history.scrollRestoration = "auto";
  };
}, []);



  const destination = result?.destination || {};

  const weather = formatWeather(
    result?.weather
  );

  const placesData = result?.places;

  const rawPlaces = useMemo(() => {
    if (Array.isArray(placesData)) {
      return placesData;
    }

    if (Array.isArray(placesData?.places)) {
      return placesData.places;
    }

    return [];
  }, [placesData]);

  const itineraryData =
    result?.itinerary || {};

  const itinerary =
    itineraryData?.itinerary ||
    itineraryData;

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
    destination.display_name ||
    trip.destination ||
    "Your Destination";

  const destinationDisplay = String(
    destinationName
  )
    .replace(/\s+/g, " ")
    .trim();

  const country =
    destination.country ||
    destination.address?.country ||
    "";


  /*
   * HERO IMAGE ONLY
   *
   * Place cards intentionally do not load
   * external images.
   */
  useEffect(() => {
    let cancelled = false;

    async function loadHeroImage() {
      const hero = await searchWikimediaImage(
        `"${destinationDisplay}"`
      );

      if (!cancelled && hero?.url) {
        setHeroImage(hero.url);
      }
    }

    loadHeroImage();

    return () => {
      cancelled = true;
    };
  }, [destinationDisplay]);

const groupedPlaces = useMemo(() => {
  const groups = {};

  // ========================================================
  // CANONICAL INTEREST ORDER
  // ========================================================

  const interestOrder = [
    "Architecture",
    "History",
    "Food",
    "Nightlife",
    "Museums",
    "Nature",
    "Shopping",
    "Adventure",
  ];

  // ========================================================
  // CATEGORY NORMALIZATION
  // ========================================================

  const categoryMap = {
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

  // ========================================================
  // INITIALIZE ALL INTEREST GROUPS
  //
  // This is important.
  // Even if one interest temporarily has no places,
  // the category still exists in the dashboard.
  // ========================================================

  interestOrder.forEach((interest) => {
    groups[interest] = [];
  });

  // ========================================================
  // GROUP PLACES USING interest_tags
  //
  // A physical place can belong to multiple interests.
  //
  // Example:
  //
  // Louvre
  // → Architecture
  // → History
  // → Museums
  //
  // The same physical place is therefore displayed in
  // all relevant interest sections.
  // ========================================================

  rawPlaces.forEach((place) => {
    if (!place || typeof place !== "object") {
      return;
    }

    // ------------------------------------------------------
    // PRIMARY / LEGACY CATEGORY
    // ------------------------------------------------------

    const primaryCategory =
      place.interest_category ||
      place.interestCategory ||
      place.interest ||
      null;

    // ------------------------------------------------------
    // MULTI-INTEREST TAGS
    // ------------------------------------------------------

    const rawTags = Array.isArray(place.interest_tags)
      ? place.interest_tags
      : [];

    const categoriesForPlace = [];

    // ------------------------------------------------------
    // ADD ALL interest_tags
    // ------------------------------------------------------

    rawTags.forEach((tag) => {
      if (!tag) {
        return;
      }

      const normalized = String(tag)
        .trim()
        .toLowerCase();

      const category =
        categoryMap[normalized] || null;

      if (
        category &&
        !categoriesForPlace.includes(category)
      ) {
        categoriesForPlace.push(category);
      }
    });

    // ------------------------------------------------------
    // ALSO ADD PRIMARY CATEGORY
    //
    // Protects compatibility with older API responses.
    // ------------------------------------------------------

    if (primaryCategory) {
      const normalizedPrimary = String(primaryCategory)
        .trim()
        .toLowerCase();

      const category =
        categoryMap[normalizedPrimary] ||
        String(primaryCategory).trim();

      if (
        category &&
        !categoriesForPlace.includes(category)
      ) {
        categoriesForPlace.push(category);
      }
    }

    // ------------------------------------------------------
    // FALLBACK
    // ------------------------------------------------------

    if (categoriesForPlace.length === 0) {
      const fallbackCategory =
        place.category
          ? String(place.category).trim()
          : "Other";

      if (!groups[fallbackCategory]) {
        groups[fallbackCategory] = [];
      }

      groups[fallbackCategory].push(place);

      return;
    }

    // ------------------------------------------------------
    // ADD PLACE TO EVERY RELEVANT INTEREST
    // ------------------------------------------------------

    categoriesForPlace.forEach((category) => {
      if (!groups[category]) {
        groups[category] = [];
      }

      groups[category].push(place);
    });
  });

  // ========================================================
  // REMOVE EMPTY INTEREST GROUPS
  //
  // We don't want empty sections such as History: 0.
  // ========================================================

  interestOrder.forEach((interest) => {
    if (
      !groups[interest] ||
      groups[interest].length === 0
    ) {
      delete groups[interest];
    }
  });

  // ========================================================
  // PRESERVE CANONICAL INTEREST ORDER
  // ========================================================

  const orderedGroups = {};

  interestOrder.forEach((interest) => {
    if (groups[interest]?.length) {
      orderedGroups[interest] = groups[interest];
    }
  });

  // ========================================================
  // KEEP ANY UNEXPECTED / LEGACY CATEGORIES
  // ========================================================

  Object.keys(groups).forEach((category) => {
    if (!orderedGroups[category]) {
      orderedGroups[category] = groups[category];
    }
  });

  return orderedGroups;
}, [rawPlaces]);

  const categories =
    Object.keys(groupedPlaces);

  const totalPlaces =
    rawPlaces.length;

  const totalActivities =
    days.reduce(
      (total, day) =>
        total +
        (Array.isArray(day.activities)
          ? day.activities.length
          : 0),
      0
    );

  const budget =
    itinerary?.budget_plan
      ?.total_budget ??
    trip?.budget ??
    "--";

  const currency =
    itinerary?.budget_plan?.currency ||
    trip?.currency ||
    "INR";

  const duration =
    itinerary?.trip_summary
      ?.duration_days ??
    trip?.days ??
    (days.length || "--");

  const getVisiblePlaces = (
    category
  ) => {
    const places =
      groupedPlaces[category] || [];

    if (
      expandedCategories[category]
    ) {
      return places;
    }

    return places.slice(0, 6);
  };

  const toggleCategory = (
    category
  ) => {
    setExpandedCategories(
      (previous) => ({
        ...previous,
        [category]:
          !previous[category],
      })
    );
  };

  return (
    <main className="destination-dashboard">
      {/* =====================================================
          NAVIGATION
      ===================================================== */}

      <nav className="dashboard-nav">
        <div className="dashboard-container dashboard-nav-inner">
          <button
            type="button"
            className="back-button"
            onClick={onBack}
          >
            <span className="back-arrow">
              ←
            </span>

            <span>
              BACK TO HOME
            </span>
          </button>

          <div className="dashboard-brand">
            <div className="dashboard-brand-mark">
              V
            </div>

            <div className="dashboard-brand-copy">
              <strong>
                VoyageMind
              </strong>

              <span>
                INTELLIGENT TRAVEL
              </span>
            </div>
          </div>

          <div className="dashboard-nav-right">
            <div className="dashboard-live">
              <span className="live-dot" />

              <span>
                JOURNEY READY
              </span>
            </div>
         </div>
        </div>
      </nav>

      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <div className="dashboard-container">
        {/* ===================================================
            DESTINATION HERO
        =================================================== */}

        <section className="destination-hero">
          <div className="destination-hero-grid" />

          <div className="destination-hero-glow" />

          {heroImage && (
            <div
              className="destination-hero-background"
              style={{
                backgroundImage: `linear-gradient(
                  180deg,
                  rgba(11, 12, 14, 0.1),
                  rgba(11, 12, 14, 0.9)
                ), url("${heroImage}")`,
              }}
            />
          )}

          <div className="destination-hero-content">
            <div className="destination-breadcrumb">
              <span>
                VOYAGEMIND
              </span>

              <i>
                /
              </i>

              <span>
                YOUR JOURNEY
              </span>
            </div>

            <div className="destination-title-row">
              <div className="destination-title-copy">
                <div className="destination-eyebrow">
                  <span>
                    ✦
                  </span>

                  YOUR PERSONALIZED ESCAPE
                </div>

                <h1>
                  {destinationDisplay}
                </h1>

                {country && (
                  <div className="destination-country">
                    {country}
                  </div>
                )}

                <p>
                  Your AI-powered travel
                  intelligence is ready.
                  Explore verified places,
                  live conditions and a
                  personalized itinerary
                  built around you.
                </p>
              </div>

              <div className="destination-ready">
                <div className="ready-icon">
                  ✓
                </div>

                <div>
                  <span>
                    AI JOURNEY
                  </span>

                  <strong>
                    READY
                  </strong>
                </div>
              </div>
            </div>

            <div className="hero-stats">
              <div className="hero-stat">
                <span className="hero-stat-icon">
                  ◷
                </span>

                <div>
                  <small>
                    DURATION
                  </small>

                  <strong>
                    {duration}{" "}
                    {duration === 1
                      ? "day"
                      : "days"}
                  </strong>
                </div>
              </div>

              <div className="hero-stat">
                <span className="hero-stat-icon">
                  ✦
                </span>

                <div>
                  <small>
                    PLACES FOUND
                  </small>

                  <strong>
                    {totalPlaces}
                  </strong>
                </div>
              </div>

              <div className="hero-stat">
                <span className="hero-stat-icon">
                  ◎
                </span>

                <div>
                  <small>
                    AI ACTIVITIES
                  </small>

                  <strong>
                    {totalActivities}
                  </strong>
                </div>
              </div>

              <div className="hero-stat">
                <span className="hero-stat-icon">
                  ◈
                </span>

                <div>
                  <small>
                    TRAVEL STYLE
                  </small>

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

        {/* ===================================================
            JOURNEY ACTIONS
        =================================================== */}

        <div className="journey-action-bar">
<button
  type="button"
  className={`journey-save-button ${
    journeySaved
      ? "saved"
      : ""
  }`}
  onClick={onSaveJourney}
  disabled={journeySaving}
>
  <span>
    {journeySaved
      ? "✓"
      : "♡"}
  </span>

  <span>
    {journeySaving
      ? "UPDATING..."
      : journeySaved
      ? "JOURNEY SAVED"
      : "SAVE JOURNEY"}
  </span>
</button>

          <button
            type="button"
            className={`journey-favorite-button ${
              isFavorite
                ? "saved"
                : ""
            }`}
            onClick={
              onToggleFavorite
            }
            disabled={
              favoriteSaving 
            }
          >
            <span>
              {isFavorite
                ? "♥"
                : "♡"}
            </span>

            <span>
              {favoriteSaving
                ? "UPDATING..."
                : isFavorite
                ? "FAVORITED"
                : "ADD TO FAVORITES"}
            </span>
          </button>
        </div>

        {/* ===================================================
            OVERVIEW
        =================================================== */}

        <section className="overview-grid">
          {/* WEATHER */}

          <article className="overview-card weather-card">
            <div className="card-topline">
              <span>
                LIVE CONDITIONS
              </span>

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
                    <small>
                      FEELS LIKE
                    </small>

                    <strong>
                      {weather.feelsLike}
                      {weather.feelsLike !==
                      "--"
                        ? "°"
                        : ""}
                    </strong>
                  </div>

                  <div>
                    <small>
                      WIND
                    </small>

                    <strong>
                      {weather.wind}
                      {weather.wind !==
                      "--"
                        ? " km/h"
                        : ""}
                    </strong>
                  </div>

                  <div>
                    <small>
                      HUMIDITY
                    </small>

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

          {/* BUDGET */}

          <article className="overview-card budget-card">
            <div className="card-topline">
              <span>
                TRIP BUDGET
              </span>

              <span>
                ◈
              </span>
            </div>

            <div className="budget-main">
              <small>
                PLANNED SPEND
              </small>

              <strong>
                {currency}{" "}
                {typeof budget ===
                "number"
                  ? budget.toLocaleString()
                  : budget}
              </strong>

              <span>
                {itinerary?.budget_plan
                  ?.estimated_daily_budget
                  ? `${currency} ${Number(
                      itinerary
                        .budget_plan
                        .estimated_daily_budget
                    ).toLocaleString()} / day`
                  : "Personalized around your selected budget"}
              </span>
            </div>

            <div className="budget-line">
              <div />
            </div>

            <p>
              {itinerary?.budget_plan
                ?.notes ||
                "Your itinerary has been planned around your selected budget."}
            </p>
          </article>

          {/* LOCATION */}

          <article className="overview-card location-card">
            <div className="card-topline">
              <span>
                DESTINATION
              </span>

              <span>
                ⌖
              </span>
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
                      ).toFixed(
                        4
                      )}°, ${Number(
                        coordinates.longitude
                      ).toFixed(
                        4
                      )}°`
                    : "Location verified"}
                </span>
              </div>
            </div>

            <button
              type="button"
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

              <span>
                ↗
              </span>
            </button>
          </article>
        </section>

        {/* ===================================================
            AI SUMMARY
        =================================================== */}

        {itinerary?.trip_summary && (
          <section className="ai-summary-section">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  ✦ VOYAGEMIND AI
                </span>

                <h2>
                  Your journey,
                  <span>
                    {" "}
                    understood.
                  </span>
                </h2>

                <p>
                  A clear overview of what
                  your trip is designed to
                  feel like.
                </p>
              </div>

              <div className="ai-badge">
                <span>
                  ✦
                </span>

                AI GENERATED
              </div>
            </div>

            <div className="ai-summary-card">
              <div className="summary-quote">
                <span className="quote-mark">
                  “
                </span>

                <p>
                  {itinerary
                    .trip_summary
                    .weather_summary ||
                    `A personalized ${duration}-day experience in ${destinationDisplay}.`}
                </p>

                <span className="quote-end">
                  ”
                </span>
              </div>

              <div className="summary-meta">
                <div>
                  <small>
                    STYLE
                  </small>

                  <strong>
                    {itinerary
                      .trip_summary
                      .travel_style ||
                      "Personalized"}
                  </strong>
                </div>

                <div>
                  <small>
                    INTERESTS
                  </small>

                  <strong>
                    {Array.isArray(
                      trip.interests
                    )
                      ? trip.interests
                          .map(
                            formatInterest
                          )
                          .join(
                            " · "
                          )
                      : "Curated for you"}
                  </strong>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ===================================================
            AI ITINERARY
        =================================================== */}

        {days.length > 0 && (
          <section className="itinerary-section">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  ✦ YOUR AI ITINERARY
                </span>

                <h2>
                  Days worth
                  <span>
                    {" "}
                    remembering.
                  </span>
                </h2>

                <p>
                  Your schedule is
                  organized around time,
                  places, interests and
                  practical pacing.
                </p>
              </div>

              <div className="itinerary-count">
                {days.length} DAYS
              </div>
            </div>

            <div className="itinerary-timeline">
              {days.map(
                (day, index) => (
                  <article
                    className="day-card"
                    key={`day-${
                      day.day ||
                      index
                    }`}
                  >
                    <div className="day-number">
                      <span>
                        DAY
                      </span>

                      <strong>
                        {String(
                          day.day ||
                            index +
                              1
                        ).padStart(
                          2,
                          "0"
                        )}
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
                            {day.day ||
                              index +
                                1}
                          </h3>
                        </div>

                        <span className="activity-count">
                          {Array.isArray(
                            day.activities
                          )
                            ? `${day.activities.length} ${
                                day
                                  .activities
                                  .length ===
                                1
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
                          <span>
                            ✦
                          </span>

                          <p>
                            {
                              day.daily_tip
                            }
                          </p>
                        </div>
                      )}
                    </div>
                  </article>
                )
              )}
            </div>
          </section>
        )}

        {/* ===================================================
            PLACES
        =================================================== */}

        <section className="places-section">
          <div className="section-heading places-heading">
            <div className="places-heading-copy">
              <span className="section-kicker">
                ✦ DISCOVER YOUR DESTINATION
              </span>

              <h2>
                Places Curated
                <span>
                  {" "}
                  for Your Trip.
                </span>
              </h2>

              <p>
                Verified locations
                organized around the
                interests you selected for
                this journey.
              </p>
            </div>

            <div className="places-total">
              <strong>
                {totalPlaces}
              </strong>

              <span>
                CURATED PLACES
              </span>
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
                Try planning another
                destination with different
                interests.
              </p>
            </div>
          ) : (
            <div className="category-list">
              {categories.map(
                (category) => {
                  const meta =
                    getCategoryMeta(
                      category
                    );

                  const places =
                    groupedPlaces[
                      category
                    ] || [];

                  const visiblePlaces =
                    getVisiblePlaces(
                      category
                    );

                  const expanded =
                    !!expandedCategories[
                      category
                    ];

                  return (
                    <section
                      className="place-category"
                      key={category}
                    >
                      <div className="category-header">
                        <div className="category-heading-content">
                          <div className="category-icon">
                            {
                              meta.icon
                            }
                          </div>

                          <div>
                            <div className="category-name-row">
                              <h3>
                                {
                                  category
                                }
                              </h3>

                              <span className="category-count">
                                {
                                  places.length
                                }{" "}
                                {places.length ===
                                1
                                  ? "PLACE"
                                  : "PLACES"}
                              </span>
                            </div>

                            <p>
                              {
                                meta.description
                              }
                            </p>
                          </div>
                        </div>

                        <div className="category-line" />
                      </div>

                      <div className="places-grid">
                        {visiblePlaces.map(
                          (
                            place,
                            placeIndex
                          ) => (
                            <article
                              className="place-card"
                              key={`${place.name}-${placeIndex}`}
                            >
                              {/* =================================
                                  FLAT PLACE VISUAL
                                  No external images.
                              ================================== */}

                              <div className="place-visual place-visual-flat">
                                <div className="place-visual-icon">
                                  {
                                    meta.icon
                                  }
                                </div>

                                <div className="place-visual-copy">
                                  <span>
                                    {String(
                                      placeIndex +
                                        1
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
                                      {
                                        category
                                      }
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
                                        .filter(
                                          Boolean
                                        )
                                        .join(
                                          ", "
                                        )}
                                  </p>
                                )}

                                {place.opening_hours && (
                                  <div className="place-hours">
                                    <span>
                                      ◷
                                    </span>

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
                                    <span>
                                      ★
                                    </span>

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
                                  type="button"
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
                          type="button"
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
                                  places.length -
                                  6
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
                }
              )}
            </div>
          )}
        </section>

        {/* ===================================================
            TRAVEL TIPS
        =================================================== */}

        {Array.isArray(
          itinerary?.travel_tips
        ) &&
          itinerary.travel_tips.length >
            0 && (
            <section className="tips-section">
              <div className="section-heading">
                <div>
                  <span className="section-kicker">
                    ✦ SMART TRAVEL
                  </span>

                  <h2>
                    Travel smarter,
                    <span>
                      {" "}
                      not harder.
                    </span>
                  </h2>

                  <p>
                    Practical guidance
                    generated for this
                    specific journey.
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
                        ).padStart(
                          2,
                          "0"
                        )}
                      </span>

                      <p>
                        {tip}
                      </p>
                    </div>
                  )
                )}
              </div>
            </section>
          )}

        {/* ===================================================
            WARNINGS
        =================================================== */}

        {Array.isArray(
          itinerary?.warnings
        ) &&
          itinerary.warnings.length >
            0 && (
            <section className="warnings-section">
              <div className="warning-header">
                <div className="warning-icon">
                  !
                </div>

                <div>
                  <span>
                    TRAVEL NOTES
                  </span>

                  <h3>
                    Keep these in mind
                  </h3>
                </div>
              </div>

              <div className="warnings-list">
                {itinerary.warnings.map(
                  (
                    warning,
                    index
                  ) => (
                    <div
                      key={index}
                    >
                      <span>
                        •
                      </span>

                      <p>
                        {warning}
                      </p>
                    </div>
                  )
                )}
              </div>
            </section>
          )}

        {/* ===================================================
            FOOTER
        =================================================== */}

        <footer className="dashboard-footer">
          <div>
            <div className="footer-brand">
              <span>
                V
              </span>

              VoyageMind
            </div>

            <p>
              Intelligent travel
              planning, built around
              you.
            </p>
          </div>

          <div className="footer-right">
            <span>
              AI GENERATED JOURNEY
            </span>

            <strong>
              ✦
            </strong>
          </div>
        </footer>
      </div>
    </main>
  );
}

export default DestinationDashboard;