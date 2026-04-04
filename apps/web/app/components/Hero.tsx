export default function Hero() {
  return (
    <section className="relative pt-28 pb-20 md:pt-36 md:pb-28 lg:pt-40 lg:pb-32 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-white to-white" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-accent/5 rounded-full blur-3xl" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Copy */}
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 text-accent text-xs font-semibold tracking-wide uppercase mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Now in Early Beta
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.1]">
              Trust every payment{" "}
              <span className="text-accent">before</span> you send it
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-slate-600 leading-relaxed max-w-lg">
              VendorCheck is an AI-powered inbox that catches suspicious vendor
              requests, bank changes, and urgent payment scams — before your
              team sends money.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-3">
              <a
                href="#join-beta"
                className="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-white bg-accent rounded-xl hover:bg-accent-hover transition-all shadow-lg shadow-accent/25 hover:shadow-xl hover:shadow-accent/30"
              >
                Join the Beta
              </a>
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-slate-700 bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all"
              >
                See How It Works
                <svg
                  className="ml-2 w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </a>
            </div>

            <p className="mt-6 text-sm text-slate-400">
              Free during beta · No credit card required · Works with your
              current tools
            </p>
          </div>

          {/* Product Mockup */}
          <div className="relative">
            <div className="relative bg-white rounded-2xl shadow-2xl shadow-slate-200/60 border border-slate-200/80 overflow-hidden">
              {/* Mockup Header */}
              <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                  <div className="w-3 h-3 rounded-full bg-slate-300" />
                </div>
                <span className="text-xs font-semibold text-slate-500 tracking-wide">
                  VENDORCHECK INBOX
                </span>
                <span className="text-xs font-medium text-slate-400">
                  3 pending
                </span>
              </div>

              {/* Inbox Items */}
              <div className="divide-y divide-slate-100">
                {/* Blocked */}
                <div className="px-5 py-4 hover:bg-slate-50/50 transition-colors">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blocked-bg text-blocked border border-blocked-border">
                      BLOCKED
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        Global Trade Corp
                      </p>
                      <p className="text-sm text-slate-500 mt-0.5">
                        Invoice #7291 — New bank account submitted
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="inline-flex items-center gap-1 text-xs text-blocked font-medium">
                          <svg
                            className="w-3 h-3"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <circle cx="10" cy="10" r="5" />
                          </svg>
                          High Risk
                        </span>
                        <span className="text-xs text-slate-400">
                          · Sender domain mismatch
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Verify */}
                <div className="px-5 py-4 bg-verify-bg/30 border-l-2 border-verify">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-verify-bg text-verify border border-verify-border">
                      VERIFY
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        ABC Medical Supplies
                      </p>
                      <p className="text-sm text-slate-500 mt-0.5">
                        Invoice #4821 — Bank details updated
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="inline-flex items-center gap-1 text-xs text-verify font-medium">
                          <svg
                            className="w-3 h-3"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <circle cx="10" cy="10" r="5" />
                          </svg>
                          Medium Risk
                        </span>
                        <span className="text-xs text-slate-400">
                          · Bank change + urgent language
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Safe */}
                <div className="px-5 py-4 hover:bg-slate-50/50 transition-colors">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-safe-bg text-safe border border-safe-border">
                      SAFE
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        Metro Office Products
                      </p>
                      <p className="text-sm text-slate-500 mt-0.5">
                        Invoice #3156 — Standard payment request
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="inline-flex items-center gap-1 text-xs text-safe font-medium">
                          <svg
                            className="w-3 h-3"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <circle cx="10" cy="10" r="5" />
                          </svg>
                          Low Risk
                        </span>
                        <span className="text-xs text-slate-400">
                          · All signals verified
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating decoration */}
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-accent/5 rounded-full blur-2xl" />
            <div className="absolute -top-4 -left-4 w-32 h-32 bg-safe/5 rounded-full blur-2xl" />
          </div>
        </div>
      </div>
    </section>
  );
}
