"use client";

import { useRouter } from "next/navigation";
import { Cloud, HardDrive, LogOut, Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth/auth-context";
import { useLlmProvider } from "@/hooks/use-llm-provider";
import { cn } from "@/lib/utils";

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const;

const LLM_PROVIDER_OPTIONS = [
  {
    value: "ollama",
    label: "Ollama",
    description: "Local model, runs on the server - default.",
    icon: HardDrive,
  },
  {
    value: "gemini",
    label: "Gemini",
    description: "Google's cloud model - needs a Gemini API key configured on the server.",
    icon: Cloud,
  },
] as const;

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { provider, setProvider } = useLlmProvider();
  const router = useRouter();

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 overflow-y-auto p-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your account information.</CardDescription>
        </CardHeader>
        <CardContent>
          <Label className="text-muted-foreground">Email</Label>
          <p className="text-sm">{user?.email}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how the app looks.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {THEME_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isActive = theme === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setTheme(option.value)}
                aria-pressed={isActive}
                className={cn(
                  "flex flex-1 flex-col items-center gap-2 rounded-lg border p-4 text-sm transition-colors",
                  isActive ? "border-primary bg-primary/5" : "hover:bg-muted/50",
                )}
              >
                <Icon className="size-4" />
                {option.label}
              </button>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI Model</CardTitle>
          <CardDescription>Choose which LLM answers your chat questions.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {LLM_PROVIDER_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isActive = provider === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setProvider(option.value)}
                aria-pressed={isActive}
                className={cn(
                  "flex flex-1 flex-col items-center gap-2 rounded-lg border p-4 text-center text-sm transition-colors",
                  isActive ? "border-primary bg-primary/5" : "hover:bg-muted/50",
                )}
              >
                <Icon className="size-4" />
                {option.label}
                <span className="text-xs text-muted-foreground">{option.description}</span>
              </button>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />
          <Button
            variant="destructive"
            onClick={() => {
              logout();
              router.push("/login");
            }}
          >
            <LogOut className="size-4" />
            Log out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
