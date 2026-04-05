"use client";

import { useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { Suspense } from "react";

function VerifyForm() {
  const { confirm } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email") ?? "";
  const [email, setEmail] = useState(emailParam);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await confirm(email, code);
      router.push("/login");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Verification failed. Check the code and try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-navy-900">Verify your email</h1>
        <p className="text-sm text-gray-500 mt-1">
          We sent a verification code to <strong>{email || "your email"}</strong>
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-blocked-bg border border-blocked-border p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {!emailParam && (
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        )}
        <Input
          label="Verification code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
          placeholder="123456"
          autoComplete="one-time-code"
          inputMode="numeric"
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Verifying…" : "Verify email"}
        </Button>
      </form>
    </Card>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyForm />
    </Suspense>
  );
}
