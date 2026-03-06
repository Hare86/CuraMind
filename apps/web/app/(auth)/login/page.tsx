"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { authApi } from "@/lib/api";
import { saveTokens, STAFF_ROLES } from "@/lib/auth";

const SALUTATIONS = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "Rev."];

const ROLE_OPTIONS = [
  { value: "", label: "Select category (default: Student)" },
  { value: "student", label: "Student" },
  { value: "psychologist", label: "Psychologist" },
  { value: "rehab_staff", label: "Rehabilitation Staff" },
  { value: "hospital_admin", label: "Hospital Administrator" },
  { value: "researcher", label: "Researcher" },
  { value: "doctor", label: "Doctor" },
];

type RegistrationState = "idle" | "student_success" | "pending_approval";

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<"login" | "register">("login");

  // Login state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Register state
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [salutation, setSalutation] = useState("");
  const [roleRequest, setRoleRequest] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [registrationState, setRegistrationState] = useState<RegistrationState>("idle");
  const [pendingRoleName, setPendingRoleName] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await authApi.login({ email, password });
      saveTokens(tokens);
      // Role-based redirect: staff/admin → dashboard, student → knowledge-bases
      const role = tokens.role ?? "student";
      if (STAFF_ROLES.includes(role)) {
        router.push("/dashboard");
      } else {
        router.push("/knowledge-bases");
      }
    } catch (err: any) {
      setError(err.message ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await authApi.register({
        email: regEmail,
        password: regPassword,
        username,
        full_name: fullName || undefined,
        salutation: salutation || undefined,
        role_request: roleRequest || undefined,
      });

      if (result.requires_login) {
        // Student registration success — redirect to login tab
        setRegistrationState("student_success");
      } else if (result.pending_approval) {
        // Non-student — pending admin approval
        setPendingRoleName(roleRequest);
        setRegistrationState("pending_approval");
      }
    } catch (err: any) {
      setError(err.message ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const isNonStudentRole = roleRequest && roleRequest !== "student";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <div className="w-full max-w-md">
        {/* CuraMind Branding */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image
              src="/curamind-logo.png"
              alt="CuraMind — Empowering Evidence-Based Care"
              width={320}
              height={160}
              className="object-contain mix-blend-multiply brightness-105 contrast-105"
              priority
            />
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            {(["login", "register"] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(""); setRegistrationState("idle"); }}
                className={`flex-1 py-3 text-sm font-semibold capitalize transition-colors
                  ${tab === t
                    ? "border-b-2 border-blue-700 text-blue-700 bg-blue-50"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                  }`}
              >
                {t === "login" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          <div className="p-8">
            {/* ── LOGIN ── */}
            {tab === "login" && (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                  <input
                    type="email"
                    className="input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@institution.edu"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                  <input
                    type="password"
                    className="input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    minLength={8}
                    required
                  />
                </div>

                {error && (
                  <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>
                )}

                <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
                  {loading ? "Signing in..." : "Sign In"}
                </button>

                <p className="text-center text-xs text-gray-500 mt-4">
                  Don&apos;t have an account?{" "}
                  <button type="button" onClick={() => setTab("register")} className="text-blue-700 font-medium hover:underline">
                    Create one
                  </button>
                </p>
              </form>
            )}

            {/* ── REGISTER ── */}
            {tab === "register" && (
              <>
                {/* Student success state */}
                {registrationState === "student_success" && (
                  <div className="text-center py-4">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">Account Created!</h3>
                    <p className="text-sm text-gray-600 mb-1">
                      Your student account has been created successfully.
                    </p>
                    <p className="text-sm text-gray-600 mb-4">
                      A confirmation email has been sent to <strong>{regEmail}</strong>.
                    </p>
                    <p className="text-sm font-medium text-blue-700 mb-6">
                      Please sign in with your registered credentials.
                    </p>
                    <button
                      onClick={() => { setTab("login"); setEmail(regEmail); setRegistrationState("idle"); }}
                      className="btn-primary w-full"
                    >
                      Go to Sign In
                    </button>
                  </div>
                )}

                {/* Pending approval state */}
                {registrationState === "pending_approval" && (
                  <div className="text-center py-4">
                    <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">Registration Pending Approval</h3>
                    <p className="text-sm text-gray-600 mb-2">
                      Your request for <strong>{pendingRoleName.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</strong> access
                      is awaiting admin review.
                    </p>
                    <p className="text-sm text-gray-500 mb-6">
                      You will receive an email notification at <strong>{regEmail}</strong> once your account is approved.
                    </p>
                    <button
                      onClick={() => { setTab("login"); setRegistrationState("idle"); }}
                      className="btn-secondary w-full"
                    >
                      Back to Sign In
                    </button>
                  </div>
                )}

                {/* Registration form */}
                {registrationState === "idle" && (
                  <form onSubmit={handleRegister} className="space-y-4">
                    {/* Salutation + Username row */}
                    <div className="flex gap-3">
                      <div className="w-28 flex-shrink-0">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Salutation <span className="text-gray-400 font-normal text-xs">(opt.)</span>
                        </label>
                        <select
                          className="input text-sm"
                          value={salutation}
                          onChange={(e) => setSalutation(e.target.value)}
                        >
                          <option value="">—</option>
                          {SALUTATIONS.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Username <span className="text-red-500">*</span></label>
                        <input
                          type="text"
                          className="input"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          placeholder="your_username"
                          minLength={3}
                          maxLength={64}
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Full Name <span className="text-gray-400 font-normal text-xs">(optional)</span>
                      </label>
                      <input
                        type="text"
                        className="input"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Dr. Jane Smith"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email Address <span className="text-red-500">*</span></label>
                      <input
                        type="email"
                        className="input"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        placeholder="you@institution.edu"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Password <span className="text-red-500">*</span></label>
                      <input
                        type="password"
                        className="input"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        placeholder="Minimum 8 characters"
                        minLength={8}
                        required
                      />
                    </div>

                    {/* User Category */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        User Category <span className="text-gray-400 font-normal text-xs">(optional)</span>
                      </label>
                      <select
                        className="input"
                        value={roleRequest}
                        onChange={(e) => setRoleRequest(e.target.value)}
                      >
                        {ROLE_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>

                      {/* Role notice */}
                      <div className={`mt-2 p-3 rounded-lg text-xs border transition-colors ${
                        isNonStudentRole
                          ? "bg-amber-50 border-amber-200 text-amber-800"
                          : "bg-blue-50 border-blue-100 text-blue-700"
                      }`}>
                        {isNonStudentRole ? (
                          <>
                            <span className="font-semibold">Approval Required:</span> Professional role access requires admin verification.
                            Your account will be reviewed before activation. You will be notified by email.
                          </>
                        ) : (
                          <>
                            <span className="font-semibold">Please Note:</span> If no category is selected, your account will default to{" "}
                            <strong>Student</strong> status. Certain advanced features and administrative privileges are restricted to
                            verified professional roles.
                          </>
                        )}
                      </div>
                    </div>

                    {error && (
                      <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>
                    )}

                    <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
                      {loading ? "Creating account..." : "Create Account"}
                    </button>
                  </form>
                )}
              </>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          &copy; {new Date().getFullYear()} CuraMind &mdash; Empowering Evidence-Based Care
        </p>
      </div>
    </div>
  );
}
