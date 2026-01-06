"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Tablet, Smartphone, Monitor, Settings2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useConversionStore } from "@/lib/store";
import { getDevices } from "@/lib/api";
import type { DeviceProfile, DeviceProfileId } from "@/types";

interface DeviceInfo {
  id: DeviceProfileId;
  icon: React.ReactNode;
  name: string;
  dimensions: string;
  manufacturer: string;
}

const DEVICE_ICONS: Record<string, React.ReactNode> = {
  kindle_basic: <Smartphone className="h-6 w-6" />,
  kindle_paperwhite_5: <Tablet className="h-6 w-6" />,
  kindle_colorsoft: <Tablet className="h-6 w-6 text-emerald-500" />,
  kindle_scribe: <Monitor className="h-6 w-6" />,
  kobo_clara_2e: <Smartphone className="h-6 w-6" />,
  kobo_libra_2: <Tablet className="h-6 w-6" />,
  kobo_sage: <Monitor className="h-6 w-6" />,
  custom: <Settings2 className="h-6 w-6" />,
};

export function DeviceSelector() {
  const t = useTranslations("device");
  const {
    imageOptions,
    setDeviceProfile,
    setImageOptions,
  } = useConversionStore();

  const [devices, setDevices] = useState<DeviceProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDevices()
      .then(setDevices)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const selectedProfile = imageOptions.device_profile;
  const isCustom = selectedProfile === "custom";

  const handleDeviceSelect = (deviceId: DeviceProfileId) => {
    setDeviceProfile(deviceId);
    if (deviceId !== "custom") {
      const device = devices.find((d) => d.id === deviceId);
      if (device) {
        setImageOptions({
          custom_width: null,
          custom_height: null,
        });
      }
    }
  };

  const deviceList: DeviceInfo[] = [
    ...devices.map((d) => ({
      id: d.id,
      icon: DEVICE_ICONS[d.id] || <Tablet className="h-6 w-6" />,
      name: d.display_name,
      dimensions: `${d.width} × ${d.height}`,
      manufacturer: d.manufacturer,
    })),
    {
      id: "custom" as DeviceProfileId,
      icon: DEVICE_ICONS.custom,
      name: t("custom"),
      dimensions: imageOptions.custom_width && imageOptions.custom_height
        ? `${imageOptions.custom_width} × ${imageOptions.custom_height}`
        : t("customDimensions"),
      manufacturer: "custom",
    },
  ];

  // Group devices by manufacturer
  const kindleDevices = deviceList.filter((d) => d.manufacturer === "kindle");
  const koboDevices = deviceList.filter((d) => d.manufacturer === "kobo");
  const customDevice = deviceList.find((d) => d.manufacturer === "custom");

  if (loading) {
    return (
      <div className="space-y-4">
        <Label>{t("title")}</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-24 bg-muted animate-pulse rounded-lg"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <Label className="text-base font-medium">{t("title")}</Label>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>

      {/* Kindle devices */}
      <div className="space-y-2">
        <Label className="text-sm text-muted-foreground">{t("kindle")}</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {kindleDevices.map((device) => (
            <Card
              key={device.id}
              className={`cursor-pointer transition-all hover:border-primary ${
                selectedProfile === device.id
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : ""
              }`}
              onClick={() => handleDeviceSelect(device.id)}
            >
              <CardContent className="p-3 flex flex-col items-center text-center gap-1">
                <div className="text-muted-foreground">{device.icon}</div>
                <div className="text-sm font-medium truncate w-full">
                  {device.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {device.dimensions}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Kobo devices */}
      <div className="space-y-2">
        <Label className="text-sm text-muted-foreground">{t("kobo")}</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {koboDevices.map((device) => (
            <Card
              key={device.id}
              className={`cursor-pointer transition-all hover:border-primary ${
                selectedProfile === device.id
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : ""
              }`}
              onClick={() => handleDeviceSelect(device.id)}
            >
              <CardContent className="p-3 flex flex-col items-center text-center gap-1">
                <div className="text-muted-foreground">{device.icon}</div>
                <div className="text-sm font-medium truncate w-full">
                  {device.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {device.dimensions}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Custom option */}
      {customDevice && (
        <div className="space-y-2">
          <Label className="text-sm text-muted-foreground">{t("customLabel")}</Label>
          <Card
            className={`cursor-pointer transition-all hover:border-primary ${
              isCustom ? "border-primary bg-primary/5 ring-1 ring-primary" : ""
            }`}
            onClick={() => handleDeviceSelect("custom")}
          >
            <CardContent className="p-3">
              <div className="flex items-center gap-3">
                <div className="text-muted-foreground">{customDevice.icon}</div>
                <div>
                  <div className="text-sm font-medium">{customDevice.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {customDevice.dimensions}
                  </div>
                </div>
              </div>

              {isCustom && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="customWidth">{t("width")}</Label>
                    <Input
                      id="customWidth"
                      type="number"
                      placeholder="1236"
                      value={imageOptions.custom_width || ""}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) =>
                        setImageOptions({
                          custom_width: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="customHeight">{t("height")}</Label>
                    <Input
                      id="customHeight"
                      type="number"
                      placeholder="1648"
                      value={imageOptions.custom_height || ""}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) =>
                        setImageOptions({
                          custom_height: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
