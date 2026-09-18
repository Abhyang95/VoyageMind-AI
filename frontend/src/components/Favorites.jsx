import { useEffect, useState } from "react";
import API from "../services/api";

const formatDate = (value) => {
  if (!value) return "";

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

function Favorites({ onBack, onViewTrip }) {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingFavoriteId, setRemovingFavoriteId] =
    useState(null);
  const [confirmFavoriteId, setConfirmFavoriteId] =
    useState(null);

  useEffect(() => {
    let cancelled = false;

    const loadFavorites = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await API.get("/favorites/");
        const savedFavorites =
          response?.data?.favorites || [];

        if (!cancelled) {
          setFavorites(savedFavorites);
        }
      } catch (requestError) {
        console.error(
          "Failed to load favorites:",
          requestError
        );

        if (!cancelled) {
          setError(
            requestError?.response?.data?.detail ||
              "Unable to load your favorites."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadFavorites();

    return () => {
      cancelled = true;
    };
  }, []);

  const removeFavorite = async (favoriteId) => {
    if (!favoriteId) return;

    try {
      setRemovingFavoriteId(favoriteId);
      setError("");

      await API.delete(
        `/favorites/${favoriteId}`
      );

      setFavorites((previousFavorites) =>
        previousFavorites.filter(
          (favorite) =>
            favorite.id !== favoriteId
        )
      );

      setConfirmFavoriteId(null);
    } catch (requestError) {
      console.error(
        "Failed to remove favorite:",
        requestError
      );

      setError(
        requestError?.response?.data?.detail ||
          "Unable to remove this favorite."
      );
    } finally {
      setRemovingFavoriteId(null);
    }
  };

  return (
    <main className="favorites-page">
      <style>{`
        /* =====================================================
           VOYAGEMIND — FAVORITES
        ===================================================== */

        .favorites-page {
          min-height: 100vh;

          padding: 0 0 90px;

          background:
            radial-gradient(
              circle at 12% 6%,
              rgba(255,255,255,.045),
              transparent 28%
            ),
            radial-gradient(
              circle at 90% 30%,
              rgba(255,255,255,.025),
              transparent 25%
            ),
            #090b0d;

          color: #f3f4f5;

          font-family: "DM Sans", sans-serif;
        }

        .favorites-page * {
          box-sizing: border-box;
        }

        .favorites-inner {
          width: min(1180px, calc(100% - 48px));

          margin: 0 auto;
        }

        /* =====================================================
           TOPBAR
        ===================================================== */

        .favorites-topbar {
          min-height: 76px;

          display: flex;

          align-items: center;

          justify-content: space-between;

          border-bottom: 1px solid rgba(255,255,255,.075);
        }

        .favorites-back {
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

        .favorites-back:hover {
          background: rgba(255,255,255,.07);

          border-color: rgba(255,255,255,.17);

          transform: translateY(-1px);
        }

        .favorites-brand {
          color: #f2f2f2;

          font-family: "Space Grotesk", sans-serif;

          font-size: 14px;

          font-weight: 600;

          letter-spacing: .18em;
        }

        .favorites-brand-subtitle {
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

        .favorites-hero {
          padding: 82px 0 58px;

          border-bottom: 1px solid rgba(255,255,255,.06);
        }

        .favorites-eyebrow {
          display: flex;

          align-items: center;

          gap: 9px;

          color: #9da2a7;

          font-size: 9px;

          font-weight: 800;

          letter-spacing: 1.8px;
        }

        .favorites-eyebrow::before {
          content: "";

          width: 22px;

          height: 1px;

          background: rgba(255,255,255,.35);
        }

        .favorites-title {
          margin: 18px 0 0;

          color: #f1f2f3;

          font-family: "Space Grotesk", sans-serif;

          font-size: clamp(52px, 7vw, 88px);

          font-weight: 500;

          line-height: .92;

          letter-spacing: -4.5px;
        }

        .favorites-title span {
          color: #777c81;
        }

        .favorites-subtitle {
          max-width: 620px;

          margin: 25px 0 0;

          color: #858a8f;

          font-size: 14px;

          line-height: 1.75;
        }

        .favorites-count {
          margin-top: 28px;

          color: rgba(255,255,255,.35);

          font-size: 8px;

          font-weight: 800;

          letter-spacing: 1.5px;
        }

        .favorites-count strong {
          color: rgba(255,255,255,.82);

          font-family: "Space Grotesk", sans-serif;

          font-size: 14px;

          margin-right: 5px;
        }

        /* =====================================================
           STATUS
        ===================================================== */

        .favorites-status {
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

        .favorites-error {
          border-color: rgba(255,150,150,.16);

          color: #dca8a8;
        }

        /* =====================================================
           GRID
        ===================================================== */

        .favorites-grid {
          display: grid;

          grid-template-columns:
            repeat(3, minmax(0, 1fr));

          gap: 18px;

          padding-top: 42px;
        }

        /* =====================================================
           CARD
        ===================================================== */

        .favorite-card {
          position: relative;

          min-height: 270px;

          display: flex;

          flex-direction: column;

          padding: 25px;

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

        .favorite-card:hover {
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

        .favorite-card::before {
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
           ICON
        ===================================================== */

        .favorite-icon {
          width: 43px;

          height: 43px;

          display: grid;

          place-items: center;

          margin-bottom: 24px;

          border: 1px solid rgba(255,255,255,.09);

          border-radius: 13px;

          background: rgba(255,255,255,.035);

          color: rgba(255,255,255,.62);

          font-size: 18px;
        }

        /* =====================================================
           CONTENT
        ===================================================== */

        .favorite-label {
          color: #777d82;

          font-size: 8px;

          font-weight: 800;

          letter-spacing: 1.5px;
        }

        .favorite-card h2 {
          margin: 9px 0 0;

          color: #f0f1f2;

          font-family: "Space Grotesk", sans-serif;

          font-size: 25px;

          font-weight: 500;

          line-height: 1.08;

          letter-spacing: -1px;
        }

        .favorite-date {
          margin-top: 10px;

          color: rgba(255,255,255,.34);

          font-size: 9px;

          letter-spacing: .3px;
        }

        /* =====================================================
           ACTIONS
        ===================================================== */

        .favorite-actions {
          display: grid;

          grid-template-columns: 1fr auto;

          gap: 8px;

          margin-top: auto;

          padding-top: 24px;
        }

        .favorite-view {
          min-height: 39px;

          padding: 0 13px;

          border: 1px solid rgba(255,255,255,.10);

          border-radius: 9px;

          background: rgba(255,255,255,.045);

          color: rgba(255,255,255,.72);

          cursor: pointer;

          text-align: left;

          font-size: 9px;

          font-weight: 800;

          letter-spacing: .75px;

          transition:
            background 180ms ease,
            border-color 180ms ease,
            color 180ms ease;
        }

        .favorite-view:hover {
          background: rgba(255,255,255,.08);

          border-color: rgba(255,255,255,.18);

          color: #fff;
        }

        .favorite-remove {
          width: 39px;

          min-height: 39px;

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

        .favorite-remove:hover {
          background: rgba(255,255,255,.055);

          border-color: rgba(255,255,255,.15);

          color: #d9d9d9;
        }

        .favorite-remove:disabled {
          opacity: .45;

          cursor: wait;
        }

        /* =====================================================
           CONFIRMATION
        ===================================================== */

        .favorite-confirm {
          margin-top: 12px;

          padding: 13px;

          border: 1px solid rgba(255,255,255,.08);

          border-radius: 10px;

          background: rgba(0,0,0,.20);
        }

        .favorite-confirm-text {
          color: rgba(255,255,255,.50);

          font-size: 9px;

          line-height: 1.5;
        }

        .favorite-confirm-actions {
          display: flex;

          gap: 7px;

          margin-top: 10px;
        }

        .favorite-confirm-button {
          min-height: 30px;

          padding: 0 10px;

          border-radius: 7px;

          cursor: pointer;

          font-size: 8px;

          font-weight: 800;

          letter-spacing: .7px;
        }

        .favorite-confirm-cancel {
          border: 1px solid rgba(255,255,255,.08);

          background: rgba(255,255,255,.03);

          color: rgba(255,255,255,.55);
        }

        .favorite-confirm-remove {
          border: 1px solid rgba(255,255,255,.13);

          background: rgba(255,255,255,.075);

          color: rgba(255,255,255,.86);
        }

        .favorite-confirm-button:disabled {
          opacity: .45;

          cursor: wait;
        }

        /* =====================================================
           EMPTY
        ===================================================== */

        .favorites-empty {
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

        .favorites-empty-icon {
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

        .favorites-empty h2 {
          margin: 0;

          color: rgba(255,255,255,.82);

          font-family: "Space Grotesk", sans-serif;

          font-size: 23px;

          font-weight: 500;
        }

        .favorites-empty p {
          max-width: 440px;

          margin: 11px auto 0;

          color: rgba(255,255,255,.38);

          font-size: 11px;

          line-height: 1.7;
        }

        /* =====================================================
           RESPONSIVE
        ===================================================== */

        @media (max-width: 960px) {
          .favorites-grid {
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 620px) {
          .favorites-inner {
            width: calc(100% - 30px);
          }

          .favorites-topbar {
            min-height: 68px;
          }

          .favorites-brand {
            font-size: 11px;
          }

          .favorites-brand-subtitle {
            display: none;
          }

          .favorites-hero {
            padding: 58px 0 45px;
          }

          .favorites-title {
            font-size: 52px;

            letter-spacing: -2.8px;
          }

          .favorites-subtitle {
            font-size: 12px;
          }

          .favorites-grid {
            grid-template-columns: 1fr;
          }

          .favorite-card {
            min-height: 245px;

            padding: 21px;
          }
        }

        @media (max-width: 390px) {
          .favorites-inner {
            width: calc(100% - 22px);
          }

          .favorites-title {
            font-size: 45px;
          }
        }
      `}</style>

      <div className="favorites-inner">
        <div className="favorites-topbar">
          <button
            type="button"
            className="favorites-back"
            onClick={onBack}
          >
            ← BACK
          </button>

          <div>
            <div className="favorites-brand">
              VOYAGEMIND
            </div>

            <div className="favorites-brand-subtitle">
              TRAVEL INTELLIGENCE
            </div>
          </div>
        </div>

        <section className="favorites-hero">
          <div className="favorites-eyebrow">
            YOUR DISCOVERIES
          </div>

          <h1 className="favorites-title">
            Favorites<span>.</span>
          </h1>

          <p className="favorites-subtitle">
            Destinations you've marked for later are
            collected here. Explore them again whenever
            inspiration strikes.
          </p>

          {!loading && !error && (
            <div className="favorites-count">
              <strong>
                {favorites.length}
              </strong>

              {favorites.length === 1
                ? "FAVORITE DESTINATION"
                : "FAVORITE DESTINATIONS"}
            </div>
          )}
        </section>

        {loading && (
          <div className="favorites-status">
            Loading your favorites...
          </div>
        )}

        {!loading && error && (
          <div className="favorites-status favorites-error">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          favorites.length === 0 && (
            <div className="favorites-empty">
              <div className="favorites-empty-icon">
                ♡
              </div>

              <h2>
                Nothing saved yet.
              </h2>

              <p>
                Favorite destinations from your
                VoyageMind journeys and they'll appear
                here for quick access.
              </p>
            </div>
          )}

        {!loading &&
          !error &&
          favorites.length > 0 && (
            <div className="favorites-grid">
              {favorites.map((favorite) => {
                const isRemoving =
                  removingFavoriteId ===
                  favorite.id;

                const isConfirming =
                  confirmFavoriteId ===
                  favorite.id;

                return (
                  <article
                    className="favorite-card"
                    key={favorite.id}
                  >
                    <div className="favorite-icon">
                      ♡
                    </div>

                    <div className="favorite-label">
                      FAVORITE DESTINATION
                    </div>

                    <h2>
                      {favorite.destination ||
                        "Unknown destination"}
                    </h2>

                    {favorite.created_at && (
                      <div className="favorite-date">
                        Added{" "}
                        {formatDate(
                          favorite.created_at
                        )}
                      </div>
                    )}

                    <div className="favorite-actions">
                      <button
                        type="button"
                        className="favorite-view"
                        onClick={() =>
                          onViewTrip?.({
                            destination:
                              favorite.destination,
                            days: 1,
                            budget: 0,
                            currency: "INR",
                            interests: [],
                            itinerary: null,
                          })
                        }
                      >
                        EXPLORE DESTINATION →
                      </button>

                      <button
                        type="button"
                        className="favorite-remove"
                        disabled={isRemoving}
                        onClick={() =>
                          setConfirmFavoriteId(
                            isConfirming
                              ? null
                              : favorite.id
                          )
                        }
                        aria-label="Remove favorite"
                        title="Remove favorite"
                      >
                        {isRemoving ? "…" : "×"}
                      </button>
                    </div>

                    {isConfirming && (
                      <div className="favorite-confirm">
                        <div className="favorite-confirm-text">
                          Remove this destination
                          from your favorites?
                        </div>

                        <div className="favorite-confirm-actions">
                          <button
                            type="button"
                            className="favorite-confirm-button favorite-confirm-cancel"
                            disabled={isRemoving}
                            onClick={() =>
                              setConfirmFavoriteId(
                                null
                              )
                            }
                          >
                            CANCEL
                          </button>

                          <button
                            type="button"
                            className="favorite-confirm-button favorite-confirm-remove"
                            disabled={isRemoving}
                            onClick={() =>
                              removeFavorite(
                                favorite.id
                              )
                            }
                          >
                            {isRemoving
                              ? "REMOVING..."
                              : "REMOVE"}
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

export default Favorites;