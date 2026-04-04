export default function ProductPreview() {
    return (
        <section className="py-20 md:py-28 bg-navy-900 relative overflow-hidden">
            {/* Background accents */}
            <div className="absolute inset-0">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
            </div>

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="max-w-2xl mx-auto text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
                        See what VendorCheck catches
                    </h2>
                    <p className="mt-4 text-lg text-slate-300 leading-relaxed">
                        Every request is analyzed for trust signals. Here&apos;s what a
                        flagged request looks like inside VendorCheck.
                    </p>
                </div>

                <div className="max-w-3xl mx-auto">
                    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                        {/* Request Header */}
                        <div className="px-6 py-4 bg-verify-bg border-b border-verify-border/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div className="flex items-center gap-3">
                                <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-verify text-white">
                                    VERIFY
                                </span>
                                <span className="text-sm font-semibold text-slate-900">
                                    Action Required
                                </span>
                            </div>
                            <span className="text-xs text-slate-500 font-mono">
                                Request #VCK-4821 · 2 min ago
                            </span>
                        </div>

                        {/* Request Body */}
                        <div className="p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-1">
                                ABC Medical Supplies updated bank details for Invoice #4821
                            </h3>
                            <p className="text-sm text-slate-500 mb-6">
                                Submitted via email from accounts@abcmedical-supplies.com
                            </p>

                            {/* Trust Signals */}
                            <div className="space-y-3 mb-6">
                                <h4 className="text-xs font-bold text-slate-400 tracking-widest uppercase">
                                    Trust Signals Detected
                                </h4>
                                <div className="space-y-2">
                                    <div className="flex items-start gap-3 p-3 bg-blocked-bg rounded-lg border border-blocked-border/50">
                                        <svg
                                            className="w-4 h-4 text-blocked mt-0.5 shrink-0"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-900">
                                                Vendor bank account changed
                                            </p>
                                            <p className="text-xs text-slate-500">
                                                Bank details differ from last 6 payments to this vendor
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start gap-3 p-3 bg-verify-bg rounded-lg border border-verify-border/50">
                                        <svg
                                            className="w-4 h-4 text-verify mt-0.5 shrink-0"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-900">
                                                Sender domain similarity detected
                                            </p>
                                            <p className="text-xs text-slate-500">
                                                abcmedical-supplies.com vs. abcmedicalsupplies.com
                                                (verified)
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start gap-3 p-3 bg-verify-bg rounded-lg border border-verify-border/50">
                                        <svg
                                            className="w-4 h-4 text-verify mt-0.5 shrink-0"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-900">
                                                Urgent payment language found
                                            </p>
                                            <p className="text-xs text-slate-500">
                                                &quot;Please update immediately&quot; and &quot;payment
                                                is overdue&quot; detected
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                                        <svg
                                            className="w-4 h-4 text-accent mt-0.5 shrink-0"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-900">
                                                Secondary approval required
                                            </p>
                                            <p className="text-xs text-slate-500">
                                                Bank change policy requires manager-level sign-off
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* System Decision */}
                            <div className="bg-slate-900 rounded-xl p-5 text-white">
                                <div className="flex items-center gap-2 mb-3">
                                    <svg
                                        className="w-5 h-5 text-verify"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                    <span className="text-sm font-bold text-verify">
                                        SYSTEM DECISION
                                    </span>
                                </div>
                                <p className="text-base font-semibold mb-2">
                                    Verify before payment
                                </p>
                                <p className="text-sm text-slate-300">
                                    Call the verified vendor contact on file at (555) 234-8910
                                    before releasing funds. Do not use the phone number in the
                                    email.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
