"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button-variants";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Search, Check, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { getCategories, updateUserTopics } from "@/lib/actions/settings";

export default function TopicSelection() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<number[]>([]);
  const [categories, setCategories] = useState<Array<{ id: number; name: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch (error) {
      console.error("Failed to load categories:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleTopic = (topicId: number) => {
    setSelectedTopics(prev =>
      prev.includes(topicId)
        ? prev.filter(id => id !== topicId)
        : [...prev, topicId]
    );
  };

  const handleContinue = async () => {
    if (selectedTopics.length < 3) return;

    setSaving(true);
    try {
      await updateUserTopics(selectedTopics);
      router.push("/onboarding/interests");
    } catch (error) {
      console.error("Failed to save topics:", error);
      alert("Failed to save topics. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const filteredTopics = categories.filter(cat =>
    cat.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen py-12 px-6 flex items-center justify-center">
        <div className="text-xl text-muted-foreground">Loading categories...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="container mx-auto max-w-5xl">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            What topics interest you?
          </h1>
          <p className="text-xl text-muted-foreground">
            Select at least 3 topics to personalize your daily brief
          </p>
        </div>

        <div className="mb-8 max-w-2xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-14 text-lg rounded-2xl"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-12">
          {filteredTopics.map((category) => (
            <Card
              key={category.id}
              onClick={() => toggleTopic(category.id)}
              className={cn(
                "p-6 cursor-pointer transition-smooth hover-lift border-2",
                selectedTopics.includes(category.id)
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-3xl">{category.icon}</span>
                {selectedTopics.includes(category.id) && (
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center animate-scale-in">
                    <Check className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </div>
              <p className="font-semibold">{category.name}</p>
            </Card>
          ))}
        </div>

        <div className="flex justify-center">
          <Button
            onClick={handleContinue}
            disabled={selectedTopics.length < 3 || saving}
            size="lg"
            className="min-w-[200px]"
          >
            {saving ? "Saving..." : `Continue (${selectedTopics.length} selected)`}
          </Button>
        </div>
      </div>
    </div>
  );
}
