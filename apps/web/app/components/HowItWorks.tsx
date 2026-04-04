export default function HowItWorks() {
    const steps = [
        {
            number: "01",
            title: "Request comes in",
            description:
                "A vendor bank change, payment request, invoice, or urgent email arrives. Forward it to VendorCheck or let it sync automatically.",
            icon: (
                <svg
                    className="w-7 h-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                    />
                </svg>
            ),
        },
        {
            number: "02",
            title: "AI checks trust signals",
            description:
                "VendorCheck scans for bank changes, sender identity, domain mismatches, urgency cues, and known risk patterns. Instantly.",
            icon: (
                <svg
                    className="w-7 h-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                    />
                </svg>
            ),
        },
        {
            number: "03",
            title: "You get a clear answer",
            description:
                "Each request gets a verdict: Safe, Verify, or Blocked. Plus a recommended action — so your team knows exactly what to do next.",
            icon: (
                <svg
                    className="w-7 h-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
                    />
                </svg>
            ),
        },
    ];

    return (
        <section id="how-it-works" className="py-20 md:py-28">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="max-w-2xl mx-auto text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                        How VendorCheck works
                    </h2>
                    <p className="mt-4 text-lg text-slate-600 leading-relaxed">
                        Three steps between a suspicious request and a costly mistake.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
                    {steps.map((step) => (
                        <div key={step.number} className="relative text-center md:text-left">
                            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-accent/10 text-accent mb-5">
                                {step.icon}
                            </div>
                            <div className="text-xs font-bold text-accent/60 tracking-widest uppercase mb-2">
                                Step {step.number}
                            </div>
                            <h3 className="text-xl font-semibold text-slate-900 mb-3">
                                {step.title}
                            </h3>
                            <p className="text-slate-600 leading-relaxed">
                                {step.description}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
