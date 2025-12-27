"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { BookOpen, ArrowRight, Zap, Shield, Download, Layers } from "lucide-react";

export default function Home() {
  const t = useTranslations("landing");
  const tNav = useTranslations("nav");

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16 md:py-24">
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="inline-flex items-center justify-center p-4 rounded-full bg-primary/10">
            <BookOpen className="h-12 w-12 text-primary" />
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            {t("hero.title")}
          </h1>

          <p className="text-xl text-muted-foreground max-w-2xl">
            {t("hero.subtitle")}
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" asChild>
              <Link href="/convert">
                {t("cta")}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="border-t bg-muted/30">
        <div className="container mx-auto px-4 py-16">
          <div className="grid md:grid-cols-4 gap-8">
            <FeatureCard
              icon={<Zap className="h-6 w-6" />}
              title={t("features.multiFormat.title")}
              description={t("features.multiFormat.description")}
            />
            <FeatureCard
              icon={<Layers className="h-6 w-6" />}
              title={t("features.merge.title")}
              description={t("features.merge.description")}
            />
            <FeatureCard
              icon={<Download className="h-6 w-6" />}
              title={t("features.metadata.title")}
              description={t("features.metadata.description")}
            />
            <FeatureCard
              icon={<Shield className="h-6 w-6" />}
              title={t("features.kindle.title")}
              description={t("features.kindle.description")}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>
            {tNav("title")} • Open Source •{" "}
            <Link
              href="https://github.com"
              className="underline underline-offset-4 hover:text-foreground"
            >
              GitHub
            </Link>
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card">
      <div className="p-3 rounded-full bg-primary/10 text-primary mb-4">
        {icon}
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
