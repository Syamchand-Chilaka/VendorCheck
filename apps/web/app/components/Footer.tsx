export default function Footer() {
  return (
    <footer className="py-12 bg-navy-950 border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
                className="fill-accent/20 stroke-accent"
                strokeWidth="1.5"
              />
              <path
                d="M9 12l2 2 4-4"
                className="stroke-accent"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-lg font-bold text-white">
              Vendor<span className="text-accent">Check</span>
            </span>
          </div>

          <div className="flex items-center gap-6">
            <a
              href="#how-it-works"
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              How It Works
            </a>
            <a
              href="#why-vendorcheck"
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              Why Us
            </a>
            <a
              href="#faq"
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              FAQ
            </a>
            <a
              href="#join-beta"
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              Join Beta
            </a>
          </div>

          <p className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} VendorCheck. All rights reserved.
          </p>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 text-center">
          <p className="text-xs text-slate-500 max-w-lg mx-auto">
            Built for early beta partners. Designed for SMB finance and ops
            teams. Works alongside your current payment stack.
          </p>
        </div>
      </div>
    </footer>
  );
}
