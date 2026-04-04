"use client";

import { useState } from "react";

const faqs = [
    {
        question: "How is VendorCheck different from AP software?",
        answer:
            "AP software manages invoices, approvals, and payment workflows. VendorCheck doesn\u2019t do any of that. We focus on one thing: checking whether a payment request is trustworthy before you act on it. Think of us as a trust filter that sits before your AP process.",
    },
    {
        question: "How is this different from payment processors?",
        answer:
            "Payment processors like Stripe or your bank move money. We don\u2019t move money at all. We verify that the request asking you to move money is legitimate. We work before the payment, not during it.",
    },
    {
        question: "Do I need to replace my current tools?",
        answer:
            "No. VendorCheck works alongside whatever you already use \u2014 QuickBooks, BILL, your bank\u2019s portal, email, spreadsheets. We add a trust layer, not another system to manage.",
    },
    {
        question: "What kinds of requests can VendorCheck review?",
        answer:
            "Vendor bank change requests, urgent payment emails, new invoice submissions, wire transfer requests, and any suspicious payment-related communication. If money is about to go somewhere, we can check it first.",
    },
    {
        question: "Is this built for large enterprises or small businesses?",
        answer:
            "VendorCheck is purpose-built for small and midsize businesses with 5 to 200 employees \u2014 the teams that handle payments without a dedicated fraud department. If you have a lean finance or ops team, this is for you.",
    },
    {
        question: "How does the verification process work?",
        answer:
            "When a request comes in, our AI scans it for risk signals: bank changes, domain mismatches, urgency cues, and policy violations. Based on the risk level, we recommend an action \u2014 approve, verify with the vendor through a known contact, or block the request entirely.",
    },
    {
        question: "Can teams define their own approval rules?",
        answer:
            "Yes. You can set rules for payment thresholds, require multi-person approvals for bank changes, enforce callback verification for certain vendors, and customize what triggers a review. Your policies, automatically enforced.",
    },
];

export default function FAQ() {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    return (
        <section id="faq" className="py-20 md:py-28">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
                        Frequently asked questions
                    </h2>
                    <p className="mt-4 text-lg text-slate-600 leading-relaxed">
                        Everything you need to know about VendorCheck.
                    </p>
                </div>

                <div className="space-y-3">
                    {faqs.map((faq, i) => (
                        <div
                            key={i}
                            className="border border-slate-200 rounded-xl overflow-hidden hover:border-slate-300 transition-colors"
                        >
                            <button
                                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                                className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded-xl"
                                aria-expanded={openIndex === i}
                            >
                                <span className="text-base font-semibold text-slate-900">
                                    {faq.question}
                                </span>
                                <svg
                                    className={`w-5 h-5 text-slate-400 shrink-0 transition-transform duration-200 ${openIndex === i ? "rotate-180" : ""
                                        }`}
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
                            </button>
                            <div
                                className={`overflow-hidden transition-all duration-300 ${openIndex === i
                                        ? "max-h-96 opacity-100"
                                        : "max-h-0 opacity-0"
                                    }`}
                            >
                                <p className="px-6 pb-5 text-slate-600 leading-relaxed">
                                    {faq.answer}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
