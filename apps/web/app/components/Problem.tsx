export default function Problem() {
    const painPoints = [
        {
            icon: (
                <svg
                    className="w-6 h-6 text-blocked"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                    />
                </svg>
            ),
            title: "Vendor bank changes slip through email",
            description:
                "A vendor emails new bank details. Your team updates the record and pays. Nobody calls to verify. That\u2019s exactly how payment fraud happens.",
        },
        {
            icon: (
                <svg
                    className="w-6 h-6 text-verify"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            ),
            title: "\u201CUrgent\u201D requests bypass normal checks",
            description:
                "A spoofed email from the CEO says \u201Cwire this today.\u201D Under pressure, someone pays first and questions later. By then, the money is gone.",
        },
        {
            icon: (
                <svg
                    className="w-6 h-6 text-slate-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                    />
                </svg>
            ),
            title: "Small teams rely on trust, not systems",
            description:
                "You don\u2019t have a 10-person fraud team. Approvals happen in email threads, Slack messages, and spreadsheets. One mistake costs thousands.",
        },
        {
            icon: (
                <svg
                    className="w-6 h-6 text-accent"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                    />
                </svg>
            ),
            title: "Existing tools don\u2019t solve this",
            description:
                "Payment platforms process payments. AP tools manage workflows. But nobody checks the trust and intent behind the request itself.",
        },
    ];

    return (
        <section className="py-20 md:py-28 bg-slate-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="max-w-2xl mx-auto text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                        Payment fraud starts before payment
                    </h2>
                    <p className="mt-4 text-lg text-slate-600 leading-relaxed">
                        Most businesses don&apos;t get hacked — they get tricked. Scams
                        start in email and succeed because nobody verifies the request
                        before sending money.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
                    {painPoints.map((point, i) => (
                        <div
                            key={i}
                            className="bg-white rounded-xl p-6 lg:p-8 border border-slate-200/80 hover:border-slate-300 hover:shadow-lg hover:shadow-slate-100 transition-all duration-300"
                        >
                            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
                                {point.icon}
                            </div>
                            <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                {point.title}
                            </h3>
                            <p className="text-slate-600 leading-relaxed">
                                {point.description}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
