import { useState } from "react";
import { createPortal } from "react-dom";

import API, {
  ACCESS_TOKEN_KEY,
  USER_KEY,
} from "../services/api";

import "./AuthModal.css";

const EMPTY_FORM = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
};

function AuthModal({
  isOpen,
  onClose,
  onAuthenticated,
}) {
  const [mode, setMode] =
    useState("login");

  const [formData, setFormData] =
    useState(EMPTY_FORM);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  if (!isOpen) {
    return null;
  }

  const resetAndClose = () => {
    if (loading) {
      return;
    }

    setMode("login");
    setFormData(EMPTY_FORM);
    setError("");

    onClose?.();
  };

  const switchMode = (
    nextMode
  ) => {
    if (loading) {
      return;
    }

    setMode(nextMode);
    setError("");

    setFormData(EMPTY_FORM);
  };

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

    if (error) {
      setError("");
    }
  };

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      setError("");

      const email =
        formData.email.trim();

      const password =
        formData.password;

      if (!email) {
        setError(
          "Please enter your email address."
        );
        return;
      }

      if (!password) {
        setError(
          "Please enter your password."
        );
        return;
      }

      if (
        mode === "register" &&
        !formData.username.trim()
      ) {
        setError(
          "Please enter a username."
        );
        return;
      }

      if (
        mode === "register" &&
        password.length < 6
      ) {
        setError(
          "Password must contain at least 6 characters."
        );
        return;
      }

      if (
        mode === "register" &&
        password !==
          formData.confirmPassword
      ) {
        setError(
          "Passwords do not match."
        );
        return;
      }

      try {
        setLoading(true);

        if (
          mode === "register"
        ) {
          const registerResponse =
            await API.post(
              "/auth/register",
              {
                username:
                  formData.username.trim(),

                email,

                password,
              }
            );

          if (
            !registerResponse
              ?.data
              ?.success
          ) {
            throw new Error(
              registerResponse
                ?.data
                ?.message ||
                "Unable to create your account."
            );
          }

          /*
           * Registration succeeds first.
           * Then we automatically log the user in.
           */
          const loginResponse =
            await API.post(
              "/auth/login",
              {
                email,
                password,
              }
            );

          const token =
            loginResponse
              ?.data
              ?.access_token;

          if (!token) {
            throw new Error(
              "Account created, but login could not be completed."
            );
          }

          localStorage.setItem(
            ACCESS_TOKEN_KEY,
            token
          );

          const authenticatedUser =
            loginResponse
              ?.data
              ?.user;

          if (
            !authenticatedUser
          ) {
            throw new Error(
              "Login succeeded, but the user profile was not returned."
            );
          }

          localStorage.setItem(
            USER_KEY,
            JSON.stringify(
              authenticatedUser
            )
          );

          onAuthenticated?.(
            authenticatedUser
          );

          setFormData(
            EMPTY_FORM
          );

          setError("");

          return;
        }

        /*
         * LOGIN
         */
        const response =
          await API.post(
            "/auth/login",
            {
              email,
              password,
            }
          );

        const token =
          response
            ?.data
            ?.access_token;

        if (!token) {
          throw new Error(
            "Login succeeded, but no access token was returned."
          );
        }

        localStorage.setItem(
          ACCESS_TOKEN_KEY,
          token
        );

        let authenticatedUser =
          response
            ?.data
            ?.user;

        /*
         * Fallback:
         * fetch the current user if login response
         * does not include the profile.
         */
        if (
          !authenticatedUser
        ) {
          const userResponse =
            await API.get(
              "/users/me"
            );

          authenticatedUser =
            userResponse?.data?.user;
        }

        if (
          !authenticatedUser
        ) {
          throw new Error(
            "Login succeeded, but the user profile was not returned."
          );
        }

        localStorage.setItem(
          USER_KEY,
          JSON.stringify(
            authenticatedUser
          )
        );

        onAuthenticated?.(
          authenticatedUser
        );

        setFormData(
          EMPTY_FORM
        );

        setError("");
      } catch (requestError) {
        console.error(
          "VoyageMind authentication error:",
          requestError
        );

        /*
         * Never leave a bad token behind.
         */
        if (
          mode === "login"
        ) {
          localStorage.removeItem(
            ACCESS_TOKEN_KEY
          );

          localStorage.removeItem(
            USER_KEY
          );
        }

        setError(
          requestError
            ?.response
            ?.data
            ?.detail ||
            requestError
              ?.response
              ?.data
              ?.message ||
            requestError?.message ||
            "Something went wrong. Please try again."
        );
      } finally {
        setLoading(false);
      }
    };

  const handleOverlayClick =
    (event) => {
      if (
        event.target ===
        event.currentTarget
      ) {
        resetAndClose();
      }
    };

  const modal = (
    <div
      className="auth-overlay"
      onMouseDown={
        handleOverlayClick
      }
      role="presentation"
    >
      <section
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        <button
          type="button"
          className="auth-close"
          onClick={
            resetAndClose
          }
          aria-label="Close authentication"
          disabled={loading}
        >
          ×
        </button>

        <div className="auth-modal-brand">
          <div className="auth-modal-brand-mark">
            V
          </div>

          <div>
            <strong>
              VoyageMind
            </strong>

            <span>
              AI TRAVEL INTELLIGENCE
            </span>
          </div>
        </div>

        <div className="auth-heading">
          <span className="auth-kicker">
            {mode === "login"
              ? "WELCOME BACK"
              : "JOIN VOYAGEMIND"}
          </span>

          <h2 id="auth-modal-title">
            {mode === "login"
              ? "Welcome back."
              : "Create your account."}
          </h2>

          <p>
            {mode === "login"
              ? "Sign in to continue planning your journeys."
              : "Create your VoyageMind account and start planning smarter journeys."}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={
              mode === "login"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode(
                "login"
              )
            }
            disabled={loading}
          >
            SIGN IN
          </button>

          <button
            type="button"
            className={
              mode ===
              "register"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode(
                "register"
              )
            }
            disabled={loading}
          >
            CREATE ACCOUNT
          </button>
        </div>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          {mode ===
            "register" && (
            <div className="auth-field">
              <label htmlFor="auth-username">
                USERNAME
              </label>

              <input
                id="auth-username"
                name="username"
                type="text"
                value={
                  formData.username
                }
                onChange={
                  handleChange
                }
                placeholder="Your username"
                autoComplete="username"
                disabled={loading}
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="auth-email">
              EMAIL
            </label>

            <input
              id="auth-email"
              name="email"
              type="email"
              value={
                formData.email
              }
              onChange={
                handleChange
              }
              placeholder="you@example.com"
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="auth-password">
              PASSWORD
            </label>

            <input
              id="auth-password"
              name="password"
              type="password"
              value={
                formData.password
              }
              onChange={
                handleChange
              }
              placeholder="Enter your password"
              autoComplete={
                mode === "login"
                  ? "current-password"
                  : "new-password"
              }
              disabled={loading}
            />
          </div>

          {mode ===
            "register" && (
            <div className="auth-field">
              <label htmlFor="auth-confirm-password">
                CONFIRM PASSWORD
              </label>

              <input
                id="auth-confirm-password"
                name="confirmPassword"
                type="password"
                value={
                  formData.confirmPassword
                }
                onChange={
                  handleChange
                }
                placeholder="Repeat your password"
                autoComplete="new-password"
                disabled={loading}
              />
            </div>
          )}

          {error && (
            <div
              className="auth-error"
              role="alert"
            >
              <span>!</span>

              <p>
                {error}
              </p>
            </div>
          )}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="auth-spinner" />

                <span>
                  {mode ===
                  "login"
                    ? "SIGNING IN..."
                    : "CREATING ACCOUNT..."}
                </span>
              </>
            ) : (
              <>
                <span>
                  {mode ===
                  "login"
                    ? "SIGN IN"
                    : "CREATE ACCOUNT"}
                </span>

                <span>
                  →
                </span>
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <span>
            {mode === "login"
              ? "New to VoyageMind?"
              : "Already have an account?"}
          </span>

          <button
            type="button"
            onClick={() =>
              switchMode(
                mode === "login"
                  ? "register"
                  : "login"
              )
            }
            disabled={loading}
          >
            {mode === "login"
              ? "Create an account"
              : "Sign in"}
          </button>
        </div>
      </section>
    </div>
  );

  return createPortal(
    modal,
    document.body
  );
}

export default AuthModal;