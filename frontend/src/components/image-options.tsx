"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Sparkles, Image, RotateCcw, Maximize } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useConversionStore } from "@/lib/store";
import { getCapabilities } from "@/lib/api";
import type { UpscaleMethod } from "@/types";

interface UpscaleOption {
  id: UpscaleMethod;
  name: string;
  description: string;
  icon: React.ReactNode;
  badge?: string;
  disabled?: boolean;
}

export function ImageOptions() {
  const t = useTranslations("imageProcessing");
  const { imageOptions, setImageOptions, setUpscaleMethod } = useConversionStore();

  const [aiAvailable, setAiAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCapabilities()
      .then((caps) => setAiAvailable(caps.ai_upscaling_available))
      .catch(() => setAiAvailable(false))
      .finally(() => setLoading(false));
  }, []);

  const upscaleOptions: UpscaleOption[] = [
    {
      id: "none",
      name: t("none"),
      description: t("noneDesc"),
      icon: <Image className="h-5 w-5" />,
    },
    {
      id: "lanczos",
      name: t("lanczos"),
      description: t("lanczosDesc"),
      icon: <Maximize className="h-5 w-5" />,
      badge: t("recommended"),
    },
    {
      id: "ai_esrgan",
      name: t("aiEsrgan"),
      description: aiAvailable ? t("aiEsrganDesc") : t("aiNotAvailable"),
      icon: <Sparkles className="h-5 w-5" />,
      badge: t("bestQuality"),
      disabled: !aiAvailable,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <Label className="text-base font-medium">{t("title")}</Label>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>

      {/* Upscale method selection */}
      <div className="space-y-3">
        <Label className="text-sm">{t("upscaleMethod")}</Label>
        <div className="grid gap-2">
          {upscaleOptions.map((option) => (
            <Card
              key={option.id}
              className={`cursor-pointer transition-all ${
                option.disabled
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:border-primary"
              } ${
                imageOptions.upscale_method === option.id && !option.disabled
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : ""
              }`}
              onClick={() => !option.disabled && setUpscaleMethod(option.id)}
            >
              <CardContent className="p-3 flex items-center gap-3">
                <div className="text-muted-foreground">{option.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{option.name}</span>
                    {option.badge && (
                      <Badge
                        variant={option.id === "lanczos" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {option.badge}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {option.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Spread detection options */}
      <div className="space-y-4">
        <Label className="text-sm">{t("spreadOptions")}</Label>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="detect-spreads" className="text-sm font-normal">
              {t("detectSpreads")}
            </Label>
            <p className="text-xs text-muted-foreground">
              {t("detectSpreadsDesc")}
            </p>
          </div>
          <Switch
            id="detect-spreads"
            checked={imageOptions.detect_spreads}
            onCheckedChange={(checked) =>
              setImageOptions({ detect_spreads: checked })
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="rotate-spreads" className="text-sm font-normal">
              {t("rotateSpreads")}
            </Label>
            <p className="text-xs text-muted-foreground">
              {t("rotateSpreadsDesc")}
            </p>
          </div>
          <Switch
            id="rotate-spreads"
            checked={imageOptions.rotate_spreads}
            disabled={!imageOptions.detect_spreads}
            onCheckedChange={(checked) =>
              setImageOptions({ rotate_spreads: checked })
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="fill-screen" className="text-sm font-normal">
              {t("fillScreen")}
            </Label>
            <p className="text-xs text-muted-foreground">
              {t("fillScreenDesc")}
            </p>
          </div>
          <Switch
            id="fill-screen"
            checked={imageOptions.fill_screen}
            onCheckedChange={(checked) =>
              setImageOptions({ fill_screen: checked })
            }
          />
        </div>
      </div>
    </div>
  );
}
