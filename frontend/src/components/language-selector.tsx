"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { Globe } from "lucide-react";
import Cookies from "js-cookie";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTranslations } from "next-intl";

const LANGUAGES = [
  { code: "en", name: "English", flag: "EN" },
  { code: "es", name: "Espanol", flag: "ES" },
] as const;

export function LanguageSelector() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const t = useTranslations("language");

  const handleLocaleChange = (locale: string) => {
    Cookies.set("locale", locale, { expires: 365 });
    startTransition(() => {
      router.refresh();
    });
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" disabled={isPending} title={t("select")}>
          <Globe className="h-5 w-5" />
          <span className="sr-only">{t("select")}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {LANGUAGES.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => handleLocaleChange(lang.code)}
          >
            <span className="mr-2 text-sm font-medium">{lang.flag}</span>
            {lang.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
