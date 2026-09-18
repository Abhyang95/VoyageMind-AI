import { useEffect, useState } from "react";
import API from "../services/api";

const formatDate = (value) => {
  if (!value) return "Not specified";

  try {
    return new Date(value).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return value;
  }
};

const formatBudget = (amount, currency = "INR") => {
  if (amount === null || amount === undefined || amount === 0) {
    return "Not specified";
  }

  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency} ${amount}`;
  }
};

function MyTrips({ onBack, onViewTrip }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingTripId, setRemovingTripId] = useState(null);
  const [confirmTripId, setConfirmTripId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const loadTrips = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await API.get("/trips/");
        const savedTrips = response?.data?.trips || [];

        if (!cancelled) {
          setTrips(savedTrips);
        }
      } catch (requestError) {
        console.error(
          "Failed to load saved trips:",
          requestError
        );

        if (!cancelled) {
          setError(
            requestError?.response?.data?.detail ||
              "Unable to load your journeys."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadTrips();

    return () => {
      cancelled = true;
    };
  }, []);

  const removeTrip = async (tripId) => {
    if (!tripId) return;

    try {
      setRemovingTripId(tripId);
      setError("");

      await API.delete(`/trips/${tripId}`);

      setTrips((previousTrips) =>
        previousTrips.filter(
          (trip) => trip.id !== tripId
        )
      );

      setConfirmTripId(null);
    } catch (requestError) {
      console.error(
        "Failed to remove saved trip:",
        requestError
      );

      setError(
        requestError?.response?.data?.detail ||
          "Unable to remove this journey."
      );
    } finally {
      setRemovingTripId(null);
    }
  };

  return (
    <main className="saved-page">
      <style>{`
        /* =====================================================
           VOYAGEMIND — MY TRIPS
        ===================================================== */

        .saved-page {
          min-height: 100vh;
          padding: 0 0 90px;

          background:
            radial-gradient(
              circle at 15% 5%,
              rgba(255,255,255,.045),
              transparent 28%
            ),
            radial-gradient(
              circle at 88% 35%,
              rgba(255,255,255,.025),
              transparent 25%
            ),
            #090b0d;

          color: #f3f4f5;

          font-family: "DM Sans", sans-serif;
        }

        .saved-page * {
          box-sizing: border-box;
        }

        .saved-page-inner {
          width: min(1180px, calc(100% - 48px));
          margin: 0 auto;
        }

        /* =====================================================
           TOP NAV
        ===================================================== */

        .saved-topbar {
          min-height: 76px;

          display: flex;
          align-items: center;
          justify-content: space-between;

          border-bottom: 1px solid rgba(255,255,255,.075);
        }

        .saved-back {
          min-height: 36px;

          display: inline-flex;
          align-items: center;
          gap: 8px;

          padding: 0 13px;

          border: 1px solid rgba(255,255,255,.10);
          border-radius: 9px;

          background: rgba(255,255,255,.035);

          color: rgba(255,255,255,.70);

          cursor: pointer;

          font-size: 9px;
          font-weight: 800;
          letter-spacing: .9px;

          transition:
            background 180ms ease,
            border-color 180ms ease,
            transform 180ms ease;
        }

        .saved-back:hover {
          background: rgba(255,255,255,.07);
          border-color: rgba(255,255,255,.17);
          transform: translateY(-1px);
        }

        .saved-brand {
          color: #f2f2f2;

          font-family: "Space Grotesk", sans-serif;

          font-size: 14px;
          font-weight: 600;

          letter-spacing: .18em;
        }

        .saved-brand-subtitle {
          color: rgba(255,255,255,.30);

          font-size: 7px;
          font-weight: 800;

          letter-spacing: .18em;

          text-align: right;

          margin-top: 3px;
        }

        /* =====================================================
           HERO
        ===================================================== */

        .saved-hero {
          padding: 82px 0 58px;

          border-bottom: 1px solid rgba(255,255,255,.06);
        }

        .saved-eyebrow {
          display: flex;
          align-items: center;
          gap: 9px;

          color: #9da2a7;

          font-size: 9px;
          font-weight: 800;

          letter-spacing: 1.8px;
        }

        .saved-eyebrow::before {
          content: "";

          width: 22px;
          height: 1px;

          background: rgba(255,255,255,.35);
        }

        .saved-title {
          margin: 18px 0 0;

          color: #f1f2f3;

          font-family: "Space Grotesk", sans-serif;

          font-size: clamp(52px, 7vw, 88px);

          font-weight: 500;

          line-height: .92;

          letter-spacing: -4.5px;
        }

        .saved-title span {
          color: #777c81;
        }

        .saved-subtitle {
          max-width: 620px;

          margin: 25px 0 0;

          color: #858a8f;

          font-size: 14px;
          line-height: 1.75;
        }

        .saved-count {
          margin-top: 28px;

          color: rgba(255,255,255,.35);

          font-size: 8px;
          font-weight: 800;

          letter-spacing: 1.5px;
        }

        .saved-count strong {
          color: rgba(255,255,255,.82);

          font-family: "Space Grotesk", sans-serif;

          font-size: 14px;

          margin-right: 5px;
        }

        /* =====================================================
           STATUS
        ===================================================== */

        .saved-status {
          margin-top: 45px;

          padding: 25px;

          border: 1px solid rgba(255,255,255,.08);
          border-radius: 17px;

          background:
            linear-gradient(
              145deg,
              rgba(255,255,255,.055),
              rgba(255,255,255,.018)
            );

          color: rgba(255,255,255,.55);

          font-size: 12px;
        }

        .saved-error {
          border-color: rgba(255,150,150,.16);
          color: #dca8a8;
        }

        /* =====================================================
           GRID
        ===================================================== */

        .saved-grid {
          display: grid;

          grid-template-columns:
            repeat(2, minmax(0, 1fr));

          gap: 18px;

          padding-top: 42px;
        }

        /* =====================================================
           CARD
        ===================================================== */

        .saved-card {
          position: relative;

          min-width: 0;

          padding: 26px;

          border: 1px solid rgba(255,255,255,.085);

          border-radius: 19px;

          background:
            linear-gradient(
              145deg,
              rgba(255,255,255,.065),
              rgba(255,255,255,.018)
            ),
            rgba(12,14,16,.80);

          box-shadow:
            inset 0 1px 0 rgba(255,255,255,.045),
            0 25px 70px rgba(0,0,0,.25);

          overflow: hidden;

          transition:
            border-color 220ms ease,
            transform 220ms ease,
            background 220ms ease;
        }

        .saved-card:hover {
          border-color: rgba(255,255,255,.14);

          background:
            linear-gradient(
              145deg,
              rgba(255,255,255,.075),
              rgba(255,255,255,.022)
            ),
            rgba(12,14,16,.86);

          transform: translateY(-2px);
        }

        .saved-card::before {
          content: "";

          position: absolute;

          left: 0;
          right: 0;
          top: 0;

          height: 1px;

          background:
            linear-gradient(
              90deg,
              transparent,
              rgba(255,255,255,.16),
              transparent
            );

          pointer-events: none;
        }

        /* =====================================================
           CARD TOP
        ===================================================== */

        .saved-card-top {
          display: flex;

          align-items: flex-start;

          justify-content: space-between;

          gap: 20px;
        }

        .saved-card-label {
          color: #777d82;

          font-size: 8px;
          font-weight: 800;

          letter-spacing: 1.6px;
        }

        .saved-card h2 {
          margin: 9px 0 0;

          color: #f0f1f2;

          font-family: "Space Grotesk", sans-serif;

          font-size: 28px;

          font-weight: 500;

          line-height: 1.05;

          letter-spacing: -1.1px;
        }

        .saved-days {
          flex-shrink: 0;

          padding: 7px 10px;

          border: 1px solid rgba(255,255,255,.09);

          border-radius: 999px;

          background: rgba(255,255,255,.035);

          color: rgba(255,255,255,.62);

          font-size: 8px;
          font-weight: 800;

          letter-spacing: 1px;
        }

        /* =====================================================
           META
        ===================================================== */

        .saved-meta {
          display: grid;

          grid-template-columns:
            repeat(2, minmax(0, 1fr));

          gap: 8px;

          margin-top: 24px;
        }

        .saved-meta-item {
          min-width: 0;

          padding: 13px;

          border: 1px solid rgba(255,255,255,.045);

          border-radius: 11px;

          background: rgba(255,255,255,.025);
        }

        .saved-meta-item span {
          display: block;

          margin-bottom: 6px;

          color: #5f656a;

          font-size: 7px;
          font-weight: 800;

          letter-spacing: 1.3px;
        }

        .saved-meta-item strong {
          display: block;

          overflow: hidden;

          text-overflow: ellipsis;

          white-space: nowrap;

          color: rgba(255,255,255,.73);

          font-family: "Space Grotesk", sans-serif;

          font-size: 11px;
          font-weight: 500;
        }

        /* =====================================================
           INTERESTS
        ===================================================== */

        .saved-interests {
          display: flex;

          flex-wrap: wrap;

          gap: 6px;

          margin-top: 17px;
        }

        .saved-interest {
          padding: 6px 9px;

          border: 1px solid rgba(255,255,255,.07);

          border-radius: 999px;

          background: rgba(255,255,255,.025);

          color: rgba(255,255,255,.44);

          font-size: 8px;
          font-weight: 700;

          letter-spacing: .5px;

          text-transform: uppercase;
        }

        /* =====================================================
           CARD ACTIONS
        ===================================================== */

        .saved-actions {
          display: grid;

          grid-template-columns: 1fr auto;

          gap: 8px;

          margin-top: 23px;

          padding-top: 17px;

          border-top: 1px solid rgba(255,255,255,.065);
        }

        .saved-view {
          min-height: 40px;

          padding: 0 15px;

          border: 1px solid rgba(255,255,255,.12);

          border-radius: 9px;

          background: rgba(255,255,255,.055);

          color: rgba(255,255,255,.82);

          cursor: pointer;

          font-size: 9px;
          font-weight: 800;

          letter-spacing: .8px;

          transition:
            background 180ms ease,
            border-color 180ms ease;
        }

        .saved-view:hover {
          background: rgba(255,255,255,.09);

          border-color: rgba(255,255,255,.19);
        }

        .saved-remove {
          min-height: 40px;

          width: 40px;

          display: grid;

          place-items: center;

          padding: 0;

          border: 1px solid rgba(255,255,255,.09);

          border-radius: 9px;

          background: rgba(255,255,255,.025);

          color: rgba(255,255,255,.40);

          cursor: pointer;

          font-size: 14px;

          transition:
            background 180ms ease,
            border-color 180ms ease,
            color 180ms ease;
        }

        .saved-remove:hover {
          background: rgba(255,255,255,.055);

          border-color: rgba(255,255,255,.15);

          color: #d9d9d9;
        }

        .saved-remove:disabled {
          opacity: .45;

          cursor: wait;
        }

        /* =====================================================
           REMOVE CONFIRMATION
        ===================================================== */

        .saved-confirm {
          margin-top: 12px;

          padding: 14px;

          border: 1px solid rgba(255,255,255,.08);

          border-radius: 11px;

          background: rgba(0,0,0,.20);
        }

        .saved-confirm-text {
          color: rgba(255,255,255,.52);

          font-size: 9px;

          line-height: 1.5;
        }

        .saved-confirm-actions {
          display: flex;

          gap: 7px;

          margin-top: 10px;
        }

        .saved-confirm-button {
          min-height: 31px;

          padding: 0 11px;

          border-radius: 7px;

          cursor: pointer;

          font-size: 8px;
          font-weight: 800;

          letter-spacing: .7px;
        }

        .saved-confirm-cancel {
          border: 1px solid rgba(255,255,255,.08);

          background: rgba(255,255,255,.03);

          color: rgba(255,255,255,.55);
        }

        .saved-confirm-remove {
          border: 1px solid rgba(255,255,255,.13);

          background: rgba(255,255,255,.075);

          color: rgba(255,255,255,.86);
        }

        .saved-confirm-button:disabled {
          opacity: .45;

          cursor: wait;
        }

        /* =====================================================
           EMPTY STATE
        ===================================================== */

        .saved-empty {
          margin-top: 42px;

          padding: 55px 35px;

          border: 1px solid rgba(255,255,255,.075);

          border-radius: 20px;

          background:
            linear-gradient(
              145deg,
              rgba(255,255,255,.045),
              rgba(255,255,255,.015)
            );

          text-align: center;
        }

        .saved-empty-icon {
          width: 54px;
          height: 54px;

          display: grid;
          place-items: center;

          margin: 0 auto 20px;

          border: 1px solid rgba(255,255,255,.09);

          border-radius: 15px;

          background: rgba(255,255,255,.035);

          color: rgba(255,255,255,.50);

          font-size: 21px;
        }

        .saved-empty h2 {
          margin: 0;

          color: rgba(255,255,255,.82);

          font-family: "Space Grotesk", sans-serif;

          font-size: 23px;

          font-weight: 500;
        }

        .saved-empty p {
          max-width: 440px;

          margin: 11px auto 0;

          color: rgba(255,255,255,.38);

          font-size: 11px;

          line-height: 1.7;
        }

        /* =====================================================
           RESPONSIVE
        ===================================================== */

        @media (max-width: 820px) {
          .saved-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 620px) {
          .saved-page-inner {
            width: calc(100% - 30px);
          }

          .saved-topbar {
            min-height: 68px;
          }

          .saved-brand {
            font-size: 11px;
          }

          .saved-brand-subtitle {
            display: none;
          }

          .saved-hero {
            padding: 58px 0 45px;
          }

          .saved-title {
            font-size: 52px;
            letter-spacing: -2.8px;
          }

          .saved-subtitle {
            font-size: 12px;
          }

          .saved-card {
            padding: 21px;
          }

          .saved-card h2 {
            font-size: 24px;
          }

          .saved-meta {
            grid-template-columns: 1fr;
          }

          .saved-actions {
            grid-template-columns: 1fr auto;
          }
        }

        @media (max-width: 390px) {
          .saved-page-inner {
            width: calc(100% - 22px);
          }

          .saved-title {
            font-size: 45px;
          }

          .saved-card {
            padding: 18px;
          }
        }
      `}</style>

      <div className="saved-page-inner">
        <div className="saved-topbar">
          <button
            type="button"
            className="saved-back"
            onClick={onBack}
          >
            ← BACK
          </button>

          <div>
            <div className="saved-brand">
              VOYAGEMIND
            </div>

            <div className="saved-brand-subtitle">
              TRAVEL INTELLIGENCE
            </div>
          </div>
        </div>

        <section className="saved-hero">
          <div className="saved-eyebrow">
            YOUR TRAVEL MEMORY
          </div>

          <h1 className="saved-title">
            My <span>journeys.</span>
          </h1>

          <p className="saved-subtitle">
            Every journey you save with VoyageMind
            stays here. Reopen your personalized
            travel intelligence whenever you need it.
          </p>

          {!loading && !error && (
            <div className="saved-count">
              <strong>{trips.length}</strong>
              {trips.length === 1
                ? "SAVED JOURNEY"
                : "SAVED JOURNEYS"}
            </div>
          )}
        </section>

        {loading && (
          <div className="saved-status">
            Loading your journeys...
          </div>
        )}

        {!loading && error && (
          <div className="saved-status saved-error">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          trips.length === 0 && (
            <div className="saved-empty">
              <div className="saved-empty-icon">
                ◫
              </div>

              <h2>
                No saved journeys yet.
              </h2>

              <p>
                Your personalized travel plans will
                appear here after you save them from
                VoyageMind.
              </p>
            </div>
          )}

        {!loading &&
          !error &&
          trips.length > 0 && (
            <div className="saved-grid">
              {trips.map((trip) => {
                const isRemoving =
                  removingTripId === trip.id;

                const isConfirming =
                  confirmTripId === trip.id;

                return (
                  <article
                    className="saved-card"
                    key={trip.id}
                  >
                    <div className="saved-card-top">
                      <div>
                        <div className="saved-card-label">
                          SAVED JOURNEY
                        </div>

                        <h2>
                          {trip.destination ||
                            "Unknown destination"}
                        </h2>
                      </div>

                      <div className="saved-days">
                        {trip.days || 1}{" "}
                        {trip.days === 1
                          ? "DAY"
                          : "DAYS"}
                      </div>
                    </div>

                    <div className="saved-meta">
                      <div className="saved-meta-item">
                        <span>DEPARTURE</span>

                        <strong>
                          {formatDate(
                            trip.departure_date
                          )}
                        </strong>
                      </div>

                      <div className="saved-meta-item">
                        <span>RETURN</span>

                        <strong>
                          {formatDate(
                            trip.return_date
                          )}
                        </strong>
                      </div>

                      <div className="saved-meta-item">
                        <span>BUDGET</span>

                        <strong>
                          {formatBudget(
                            trip.budget,
                            trip.currency || "INR"
                          )}
                        </strong>
                      </div>

                      <div className="saved-meta-item">
                        <span>SAVED ON</span>

                        <strong>
                          {formatDate(
                            trip.created_at
                          )}
                        </strong>
                      </div>
                    </div>

                    {Array.isArray(trip.interests) &&
                      trip.interests.length > 0 && (
                        <div className="saved-interests">
                          {trip.interests.map(
                            (interest) => (
                              <span
                                className="saved-interest"
                                key={`${trip.id}-${interest}`}
                              >
                                {interest}
                              </span>
                            )
                          )}
                        </div>
                      )}

                    <div className="saved-actions">
                      <button
                        type="button"
                        className="saved-view"
                        onClick={() =>
                          onViewTrip?.(trip)
                        }
                      >
                        VIEW JOURNEY →
                      </button>

                      <button
                        type="button"
                        className="saved-remove"
                        disabled={isRemoving}
                        onClick={() =>
                          setConfirmTripId(
                            isConfirming
                              ? null
                              : trip.id
                          )
                        }
                        aria-label="Remove saved journey"
                        title="Remove journey"
                      >
                        {isRemoving ? "…" : "×"}
                      </button>
                    </div>

                    {isConfirming && (
                      <div className="saved-confirm">
                        <div className="saved-confirm-text">
                          Remove this saved journey
                          permanently?
                        </div>

                        <div className="saved-confirm-actions">
                          <button
                            type="button"
                            className="saved-confirm-button saved-confirm-cancel"
                            disabled={isRemoving}
                            onClick={() =>
                              setConfirmTripId(null)
                            }
                          >
                            CANCEL
                          </button>

                          <button
                            type="button"
                            className="saved-confirm-button saved-confirm-remove"
                            disabled={isRemoving}
                            onClick={() =>
                              removeTrip(trip.id)
                            }
                          >
                            {isRemoving
                              ? "REMOVING..."
                              : "REMOVE JOURNEY"}
                          </button>
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
      </div>
    </main>
  );
}

export default MyTrips;