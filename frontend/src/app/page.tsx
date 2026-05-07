"use client";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  BookOpen,
  Shield,
  Zap,
  GitBranch,
  MessageSquare,
  FileText,
  Link2,
  Users,
  CheckCircle2,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: FileText,
    title: "Document Intelligence",
    description:
      "Upload PRDs, architecture docs, runbooks, and more. Our AI understands the context and relationships between documents.",
  },
  {
    icon: Link2,
    title: "Confluence & Wiki Scraping",
    description:
      "Paste Confluence links and we'll scrape, parse, and index the content automatically — always up to date.",
  },
  {
    icon: GitBranch,
    title: "Code Repository Integration",
    description:
      "Connect GitHub or GitLab repos. Help developers understand codebase structure, setup steps, and conventions.",
  },
  {
    icon: MessageSquare,
    title: "AI-Powered Q&A",
    description:
      "Developers ask questions in natural language. Get answers with source links, code snippets, and setup guides.",
  },
  {
    icon: Shield,
    title: "Enterprise-Grade Privacy",
    description:
      "Your data stays private. Organization-level isolation ensures no cross-tenant data leakage.",
  },
  {
    icon: Users,
    title: "Role-Based Access",
    description:
      "Project leads upload content. Developers consume it. Admins manage everything. Clear separation of concerns.",
  },
];

const steps = [
  {
    number: "01",
    title: "Create a Project",
    description: "Set up a project space for your team or product.",
  },
  {
    number: "02",
    title: "Add Knowledge Sources",
    description: "Upload docs, paste Confluence links, connect repos.",
  },
  {
    number: "03",
    title: "Invite Developers",
    description: "New hires get instant access to project knowledge.",
  },
  {
    number: "04",
    title: "Ask Anything",
    description: "AI answers with context, sources, and setup guidance.",
  },
];

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="container flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-lg text-foreground">
              DevOnboard
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a
              href="#features"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              How it Works
            </a>
            <a
              href="#pricing"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Pricing
            </a>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/login")}
            >
              Sign in
            </Button>
            <Button
              variant="hero"
              size="sm"
              onClick={() => router.push("/login")}
            >
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 relative overflow-hidden">
        <div className="absolute inset-0 gradient-subtle opacity-50" />
        <div className="container relative">
          <motion.div
            className="max-w-3xl mx-auto text-center"
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
            }}
          >
            <motion.div variants={fadeUp} custom={0}>
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent text-accent-foreground text-xs font-medium mb-6">
                <Zap className="w-3 h-3" /> AI-Powered Developer Onboarding
              </span>
            </motion.div>
            <motion.h1
              variants={fadeUp}
              custom={1}
              className="font-display text-4xl md:text-6xl font-bold tracking-tight text-foreground leading-[1.1] mb-6"
            >
              Onboard developers in{" "}
              <span className="text-gradient">minutes, not months</span>
            </motion.h1>
            <motion.p
              variants={fadeUp}
              custom={2}
              className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed"
            >
              Upload your docs, connect your repos, paste your Confluence links.
              DevOnboard creates an AI knowledge base that answers any question
              about your project — instantly.
            </motion.p>
            <motion.div
              variants={fadeUp}
              custom={3}
              className="flex items-center justify-center gap-4"
            >
              <Button
                variant="hero"
                size="lg"
                onClick={() => router.push("/login")}
              >
                Start Free Trial <ArrowRight className="w-4 h-4" />
              </Button>
              <Button variant="hero-outline" size="lg" asChild>
                <a href="#how-it-works">See How It Works</a>
              </Button>
            </motion.div>
            <motion.div
              variants={fadeUp}
              custom={4}
              className="mt-8 flex items-center justify-center gap-6 text-sm text-muted-foreground"
            >
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-success" /> No credit
                card required
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-success" /> Setup in 5
                minutes
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-success" /> Enterprise
                ready
              </span>
            </motion.div>
          </motion.div>

          {/* Hero visual */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="mt-16 max-w-4xl mx-auto"
          >
            <div className="rounded-xl border border-border bg-card shadow-elevated overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-surface-elevated">
                <div className="w-3 h-3 rounded-full bg-destructive/50" />
                <div className="w-3 h-3 rounded-full bg-warning/50" />
                <div className="w-3 h-3 rounded-full bg-success/50" />
                <span className="ml-2 text-xs text-muted-foreground font-mono">
                  DevOnboard — Project: E-Commerce Platform
                </span>
              </div>
              <div className="p-6 grid md:grid-cols-3 gap-4">
                <div className="md:col-span-1 space-y-3">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
                    Knowledge Sources
                  </div>
                  {[
                    "Architecture Overview.pdf",
                    "API Documentation",
                    "Confluence: Setup Guide",
                    "GitHub: main repo",
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-accent text-sm text-foreground"
                    >
                      <FileText className="w-3.5 h-3.5 text-primary" />
                      <span className="truncate">{item}</span>
                    </div>
                  ))}
                </div>
                <div className="md:col-span-2 bg-background rounded-lg border border-border p-4">
                  <div className="space-y-4">
                    <div className="flex justify-end">
                      <div className="gradient-primary rounded-lg rounded-br-sm px-4 py-2 text-sm text-white max-w-[80%]">
                        How do I set up the local development environment?
                      </div>
                    </div>
                    <div className="flex justify-start">
                      <div className="bg-accent rounded-lg rounded-bl-sm px-4 py-2 text-sm text-foreground max-w-[85%]">
                        <p className="mb-2">
                          Based on the{" "}
                          <span className="font-medium text-primary">
                            Setup Guide
                          </span>{" "}
                          and repo README, here&apos;s how to get started:
                        </p>
                        <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                          <li>
                            Clone the repo:{" "}
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              git clone ...
                            </code>
                          </li>
                          <li>
                            Install dependencies:{" "}
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              npm install
                            </code>
                          </li>
                          <li>
                            Copy{" "}
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              .env.example
                            </code>{" "}
                            to{" "}
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              .env
                            </code>
                          </li>
                          <li>
                            Run{" "}
                            <code className="text-xs bg-muted px-1 py-0.5 rounded">
                              docker-compose up
                            </code>
                          </li>
                        </ol>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Source:{" "}
                          <span className="text-primary underline cursor-pointer">
                            Confluence: Setup Guide
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-background">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-4">
              Everything your team needs to onboard fast
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              From document ingestion to intelligent Q&A, DevOnboard covers
              every aspect of developer onboarding.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group p-6 rounded-xl border border-border bg-card hover:shadow-elevated hover:border-primary/20 transition-all duration-300"
              >
                <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center mb-4 group-hover:gradient-primary transition-all duration-300">
                  <feature.icon className="w-5 h-5 text-primary group-hover:text-white transition-colors" />
                </div>
                <h3 className="font-display font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 gradient-subtle">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-4">
              Up and running in 4 simple steps
            </h2>
          </div>
          <div className="max-w-3xl mx-auto grid md:grid-cols-2 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="flex gap-4"
              >
                <div className="text-3xl font-display font-bold text-gradient">
                  {step.number}
                </div>
                <div>
                  <h3 className="font-display font-semibold text-foreground mb-1">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="pricing" className="py-20 bg-background">
        <div className="container">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-4">
              Ready to transform developer onboarding?
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              Start your free trial today. No credit card required.
            </p>
            <Button
              variant="hero"
              size="lg"
              onClick={() => router.push("/login")}
            >
              Get Started Free <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border bg-background">
        <div className="container flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded gradient-primary flex items-center justify-center">
              <BookOpen className="w-3 h-3 text-white" />
            </div>
            <span className="font-display font-semibold text-sm text-foreground">
              DevOnboard
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            &copy; 2026 DevOnboard. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
