"use client";

import { useState, type FormEvent } from "react";

export default function FinalCTA() {
    const [email, setEmail] = useState("");
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (email.trim()) {
            setSubmitted(true);
        }
    };

    return (
        <section
            id="join-beta"
            className="py-20 md:py-28 bg-slate-900 relative overflow-hidden"
        >
            <div className="absolute inset-0">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/10 rounded-full blur-3xl" />
            </div>

            <div className="relative max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
                    Stop risky payments before they leave your account
                </h2>
                <p className="mt-4 text-lg text-slate-300 leading-relaxed max-w-lg mx-auto">
                    Join the VendorCheck beta and be one of the first teams to get a trust
                    layer for every payment request.
                </p>

                {submitted ? (
                    <div className="mt-10 inline-flex items-center gap-3 px-6 py-4 bg-safe/10 border border-safe/30 rounded-xl">
                        <svg
                            className="w-6 h-6 text-safe"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                        <span className="text-white font-medium">
                            You&apos;re on the list. We&apos;ll be in touch soon.
                        </span>
                    </div>
                ) : (
                    <form
                        onSubmit={handleSubmit}
                        className="mt-10 flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
                    >
                        <label htmlFor="beta-email" className="sr-only">
                            Work email
                        </label>
                        <input
                            id="beta-email"
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your work email"
                            className="flex-1 px-4 py-3.5 rounded-xl bg-white/10 border border-white/20 text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
                        />
                        <button
                            type="submit"
                            className="px-7 py-3.5 text-sm font-semibold text-white bg-accent rounded-xl hover:bg-accent-hover transition-colors shadow-lg shadow-accent/25 whitespace-nowrap"
                        >
                            Join the Beta
                        </button>
                    </form>
                )}

                <p className="mt-5 text-xs text-slate-500">
                    Free during beta · No credit card required · Cancel anytime
                </p>
            </div>
        </section>
    );
}
