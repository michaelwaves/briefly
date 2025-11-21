import { auth } from "@/auth";
import { redirect } from "next/navigation";
import React from "react";
import Link from "next/link";
import { Radio } from "lucide-react";
import SignOutButton from "@/components/auth/SignOutButton";

async function DashboardLayoutPage({ children }: { children: React.ReactNode }) {
    const session = await auth()
    if (!session?.user) {
        redirect("/login")
    }
    return (
        <div>
            <nav className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
                <div className="container mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/d" className="flex items-center gap-2">
                        <Radio className="h-6 w-6 text-primary" />
                        <span className="text-xl font-bold lowercase">briefly</span>
                    </Link>
                    <SignOutButton />
                </div>
            </nav>
            {children}
        </div>
    );
}

export default DashboardLayoutPage;
