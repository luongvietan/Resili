import { NavBar } from "@/components/layout/NavBar";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Pricing } from "@/components/landing/Pricing";
import { Footer } from "@/components/layout/Footer";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-canvas">
      <NavBar />
      <main className="flex-1">
        <Hero />
        <Features />
        <Pricing />
      </main>
      <Footer />
    </div>
  );
}
