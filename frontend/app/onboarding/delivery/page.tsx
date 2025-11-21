"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button-variants";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Music, Rss, Copy, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export default function DeliverySetup() {
  const router = useRouter();
  const { toast } = useToast();
  const [deliveryMethod, setDeliveryMethod] = useState<"spotify" | "rss">("spotify");
  const [frequency, setFrequency] = useState<"daily" | "weekly">("daily");
  const [copied, setCopied] = useState(false);

  const mockRssFeed = "https://briefly.com/feed/user123abc";

  const handleSpotifyConnect = () => {
    toast({
      title: "Spotify Connected!",
      description: "Your brief will be delivered to Spotify daily.",
    });
    setTimeout(() => {
      router.push("/d");
    }, 1000);
  };

  const handleRssSetup = () => {
    localStorage.setItem("briefly_delivery", JSON.stringify({ method: "rss", frequency }));
    router.push("/d");
  };

  const copyRssFeed = () => {
    navigator.clipboard.writeText(mockRssFeed);
    setCopied(true);
    toast({
      title: "RSS Feed Copied!",
      description: "Add this to your favorite podcast app to receive daily briefs.",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="container mx-auto max-w-3xl">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            How would you like to receive your brief?
          </h1>
          <p className="text-xl text-muted-foreground">
            Connect Spotify or get an RSS feed for any podcast app
          </p>
        </div>

        <Card className="p-8 shadow-large border-0 mb-8">
          <div className="mb-8">
            <div
              onClick={() => setDeliveryMethod("spotify")}
              className={cn(
                "p-6 rounded-2xl border-2 cursor-pointer transition-smooth",
                deliveryMethod === "spotify" ? "border-spotify bg-spotify/5" : "border-border"
              )}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-spotify flex items-center justify-center">
                  <Music className="h-6 w-6 text-spotify-foreground" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold">Connect to Spotify</h3>
                  <p className="text-sm text-muted-foreground">Seamlessly sync to your library</p>
                </div>
              </div>
              {deliveryMethod === "spotify" && (
                <Button
                  variant="spotify"
                  className="w-full"
                  onClick={handleSpotifyConnect}
                >
                  <Music className="h-5 w-5 mr-2" />
                  Connect Spotify Account
                </Button>
              )}
            </div>
          </div>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-card px-4 text-muted-foreground">or</span>
            </div>
          </div>

          <div>
            <div
              onClick={() => setDeliveryMethod("rss")}
              className={cn(
                "p-6 rounded-2xl border-2 cursor-pointer transition-smooth",
                deliveryMethod === "rss" ? "border-primary bg-primary/5" : "border-border"
              )}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Rss className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold">Use RSS Feed</h3>
                  <p className="text-sm text-muted-foreground">Works with any podcast app</p>
                </div>
              </div>
              {deliveryMethod === "rss" && (
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm mb-2 block">Your RSS Feed URL</Label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={mockRssFeed}
                        readOnly
                        className="flex-1 h-12 px-4 rounded-xl bg-muted text-sm font-mono"
                      />
                      <Button onClick={copyRssFeed} size="icon" variant="outline">
                        {copied ? <Check className="h-5 w-5" /> : <Copy className="h-5 w-5" />}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-8 shadow-large border-0 mb-8">
          <h3 className="text-xl font-bold mb-6">Delivery Frequency</h3>
          <RadioGroup value={frequency} onValueChange={(v) => setFrequency(v as "daily" | "weekly")}>
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-4 rounded-xl border-2 border-border hover:border-primary/50 transition-smooth cursor-pointer">
                <RadioGroupItem value="daily" id="daily" />
                <Label htmlFor="daily" className="flex-1 cursor-pointer">
                  <div className="font-semibold">Daily</div>
                  <div className="text-sm text-muted-foreground">Get your brief every morning</div>
                </Label>
              </div>
              <div className="flex items-center space-x-3 p-4 rounded-xl border-2 border-border hover:border-primary/50 transition-smooth cursor-pointer">
                <RadioGroupItem value="weekly" id="weekly" />
                <Label htmlFor="weekly" className="flex-1 cursor-pointer">
                  <div className="font-semibold">Weekly</div>
                  <div className="text-sm text-muted-foreground">Receive a comprehensive weekly summary</div>
                </Label>
              </div>
            </div>
          </RadioGroup>
        </Card>

        <div className="flex justify-center">
          <Button
            onClick={deliveryMethod === "spotify" ? handleSpotifyConnect : handleRssSetup}
            size="lg"
            className="min-w-[200px]"
          >
            Finish Setup
          </Button>
        </div>
      </div>
    </div>
  );
}
