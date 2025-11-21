"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button-variants";
import { BookOpen, ChevronLeft, ChevronRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { getArticlesByCategories, updateUserPreferenceVector, getUserSettings } from "@/lib/actions/settings";
import { useToast } from "@/hooks/use-toast";

interface Article {
  id: number;
  text: string;
  summary: string | null;
  source: string | null;
  date_written: Date | null;
  category_id: number | null;
}

export default function InterestsSelection() {
  const router = useRouter();
  const { toast } = useToast();
  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedArticles, setSelectedArticles] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [categoryIds, setCategoryIds] = useState<number[]>([]);

  useEffect(() => {
    loadUserCategoriesAndArticles();
  }, []);

  useEffect(() => {
    if (categoryIds.length > 0) {
      loadArticles(currentPage);
    }
  }, [currentPage, categoryIds]);

  const loadUserCategoriesAndArticles = async () => {
    try {
      const settings = await getUserSettings();
      if (!settings?.category_ids || settings.category_ids.length === 0) {
        toast({
          title: "No categories selected",
          description: "Please select your topics first.",
          variant: "destructive",
        });
        router.push("/onboarding/topics");
        return;
      }
      setCategoryIds(settings.category_ids);
    } catch (error) {
      console.error("Failed to load settings:", error);
      toast({
        title: "Error",
        description: "Failed to load your settings. Please try again.",
        variant: "destructive",
      });
    }
  };

  const loadArticles = async (page: number) => {
    setLoading(true);
    try {
      const result = await getArticlesByCategories(categoryIds, page, 10);
      setArticles(result.articles);
      setTotalPages(result.totalPages);
    } catch (error) {
      console.error("Failed to load articles:", error);
      toast({
        title: "Error",
        description: "Failed to load articles. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleArticle = (articleId: number) => {
    setSelectedArticles(prev => {
      if (prev.includes(articleId)) {
        return prev.filter(id => id !== articleId);
      }
      if (prev.length >= 5) {
        toast({
          title: "Maximum reached",
          description: "You can only select up to 5 articles.",
        });
        return prev;
      }
      return [...prev, articleId];
    });
  };

  const handleContinue = async () => {
    if (selectedArticles.length !== 5) {
      toast({
        title: "Selection incomplete",
        description: "Please select exactly 5 articles to continue.",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      await updateUserPreferenceVector(selectedArticles);
      toast({
        title: "Preferences saved!",
        description: "We'll use your interests to personalize your content.",
      });
      router.push("/onboarding/length");
    } catch (error) {
      console.error("Failed to save preferences:", error);
      toast({
        title: "Error",
        description: "Failed to save your preferences. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (date: Date | null) => {
    if (!date) return "";
    return new Date(date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  };

  if (loading && articles.length === 0) {
    return (
      <div className="min-h-screen py-12 px-6 flex items-center justify-center">
        <div className="text-xl text-muted-foreground">Loading articles...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-6">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-12 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <BookOpen className="h-8 w-8 text-primary" />
            <h1 className="text-4xl md:text-5xl font-bold">
              What interests you?
            </h1>
          </div>
          <p className="text-xl text-muted-foreground mb-4">
            Select 5 articles that seem interesting to help us personalize your content
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-medium">
            <Check className="h-4 w-4" />
            {selectedArticles.length} / 5 selected
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {articles.map((article) => (
            <Card
              key={article.id}
              onClick={() => !saving && toggleArticle(article.id)}
              className={cn(
                "p-6 cursor-pointer transition-smooth hover-lift border-2",
                selectedArticles.includes(article.id)
                  ? "border-primary bg-primary/5 shadow-large"
                  : "border-border hover:border-primary/50",
                saving && "opacity-50 cursor-not-allowed"
              )}
            >
              <div className="flex items-start gap-4">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-smooth",
                  selectedArticles.includes(article.id)
                    ? "bg-primary"
                    : "bg-muted"
                )}>
                  {selectedArticles.includes(article.id) && (
                    <Check className="h-4 w-4 text-primary-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
                    {article.source && <span>{article.source}</span>}
                    {article.date_written && (
                      <>
                        <span>•</span>
                        <span>{formatDate(article.date_written)}</span>
                      </>
                    )}
                  </div>
                  <h3 className="font-semibold mb-2 line-clamp-2">
                    {article.summary || article.text.substring(0, 100)}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {article.text.substring(0, 200)}...
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 mb-8">
            <Button
              variant="outline"
              onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
              disabled={currentPage === 0 || loading}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1 || loading}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        )}

        <div className="flex justify-center">
          <Button
            onClick={handleContinue}
            disabled={selectedArticles.length !== 5 || saving}
            size="lg"
            className="min-w-[200px]"
          >
            {saving ? "Saving..." : "Continue"}
          </Button>
        </div>

        <div className="text-center mt-8 text-sm text-muted-foreground">
          Your selections help us understand your preferences better
        </div>
      </div>
    </div>
  );
}
