import { useState } from "react";
import { login, register } from "../api/client";

interface AuthProps {
  onAuthenticated: (token: string) => void;
}

export default function Auth({ onAuthenticated }: AuthProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password, fullName || undefined);
      }
      const token = await login(email, password);
      localStorage.setItem("access_token", token);
      onAuthenticated(token);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <div className="field">
              <label>Full name</label>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
          )}
          <div className="field">
            <label>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Register"}
          </button>
        </form>
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: 16, fontSize: 13 }}>
          {mode === "login" ? (
            <span>
              No account?{" "}
              <a href="#" onClick={() => setMode("register")}>
                Register
              </a>
            </span>
          ) : (
            <span>
              Already have an account?{" "}
              <a href="#" onClick={() => setMode("login")}>
                Sign in
              </a>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}