import Header from "./components/Header";
import Hero from "./components/Hero";
import Problem from "./components/Problem";
import HowItWorks from "./components/HowItWorks";
import WhyDifferent from "./components/WhyDifferent";
import UseCases from "./components/UseCases";
import ProductPreview from "./components/ProductPreview";
import FAQ from "./components/FAQ";
import FinalCTA from "./components/FinalCTA";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <WhyDifferent />
        <UseCases />
        <ProductPreview />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
