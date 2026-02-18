import { motion, useScroll, useTransform } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  FileText, Search, Brain, BarChart3, Shield, Zap, 
  Upload, Layers, MessageSquare, TrendingUp, ArrowRight,
  ChevronRight, Sparkles, GitCompare,
  DollarSign, PieChart, Activity, BookOpen
} from 'lucide-react'
import { useRef } from 'react'

// Floating particle component
function FloatingIcon({ icon: Icon, delay, x, y, size = 24 }: { 
  icon: any, delay: number, x: string, y: string, size?: number 
}) {
  return (
    <motion.div
      className="absolute text-primary/20 pointer-events-none"
      style={{ left: x, top: y }}
      animate={{
        y: [0, -20, 0],
        x: [0, 10, 0],
        rotate: [0, 5, -5, 0],
        opacity: [0.15, 0.3, 0.15],
      }}
      transition={{
        duration: 6,
        delay,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      <Icon size={size} />
    </motion.div>
  )
}

// Animated counter
function AnimatedCounter({ value, suffix = '', label }: { value: number, suffix?: string, label: string }) {
  return (
    <motion.div 
      className="text-center"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      <motion.p 
        className="text-4xl md:text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        {value}{suffix}
      </motion.p>
      <p className="text-gray-400 mt-2 text-sm">{label}</p>
    </motion.div>
  )
}

// Feature card
function FeatureCard({ icon: Icon, title, description, delay }: {
  icon: any, title: string, description: string, delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -8, scale: 1.02 }}
      className="group relative glass p-6 rounded-2xl overflow-hidden cursor-default"
    >
      {/* Hover glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative z-10">
        <div className="w-12 h-12 rounded-xl bg-gradient-primary/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
          <Icon className="text-primary" size={24} />
        </div>
        <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
        <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
      </div>
      
      {/* Bottom glow line */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-primary transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left" />
    </motion.div>
  )
}

// Pipeline step
function PipelineStep({ step, title, description, icon: Icon, isLast, delay }: {
  step: number, title: string, description: string, icon: any, isLast: boolean, delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -30 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className="flex items-start gap-4"
    >
      <div className="flex flex-col items-center flex-shrink-0">
        <div className="w-12 h-12 rounded-full bg-gradient-primary flex items-center justify-center text-white font-bold shadow-lg shadow-primary/30">
          <Icon size={20} />
        </div>
        {!isLast && (
          <motion.div 
            className="w-0.5 h-16 bg-gradient-to-b from-primary/50 to-transparent mt-2"
            initial={{ scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: delay + 0.3 }}
          />
        )}
      </div>
      <div className="pt-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-primary text-xs font-mono">STEP {step}</span>
        </div>
        <h4 className="text-white font-semibold text-lg">{title}</h4>
        <p className="text-gray-400 text-sm mt-1 leading-relaxed">{description}</p>
      </div>
    </motion.div>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll()
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0])
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.95])

  const features = [
    {
      icon: MessageSquare,
      title: 'Smart Document Chat',
      description: 'Ask natural language questions about your financial documents and get context-aware answers with citations.',
    },
    {
      icon: Zap,
      title: 'Real-time Streaming',
      description: 'Watch answers appear token-by-token with SSE streaming for a responsive, interactive experience.',
    },
    {
      icon: Sparkles,
      title: 'AI Executive Summaries',
      description: 'Get structured summaries with sentiment analysis, key takeaways, and bull/bear investment cases.',
    },
    {
      icon: BarChart3,
      title: 'Financial Dashboards',
      description: 'Auto-extracted metrics, key ratios (ROE, EPS, P/E), and financial highlights from your documents.',
    },
    {
      icon: GitCompare,
      title: 'Multi-Doc Comparison',
      description: 'Compare multiple annual reports side-by-side with AI-powered dimensional analysis.',
    },
    {
      icon: Shield,
      title: 'Reduced Hallucinations',
      description: 'RAG-grounded answers with source citations ensure factual correctness vs. plain LLM responses.',
    },
  ]

  const pipeline = [
    {
      icon: Upload,
      title: 'Upload Financial Documents',
      description: 'Upload PDFs — annual reports, 10-K filings, balance sheets, earnings call transcripts.',
    },
    {
      icon: Layers,
      title: 'Smart Semantic Chunking',
      description: 'Documents are intelligently split into chunks preserving tables, headers, and narrative context.',
    },
    {
      icon: Search,
      title: 'Vector Retrieval & Reranking',
      description: 'ChromaDB embeddings + cross-encoder reranking finds the most relevant passages for your query.',
    },
    {
      icon: Brain,
      title: 'LLM-Powered Answers',
      description: 'GPT-4 / LLaMA-3 generates accurate, cited answers grounded in the retrieved financial context.',
    },
  ]

  const techStack = [
    { name: 'FastAPI', color: '#009688' },
    { name: 'React', color: '#61DAFB' },
    { name: 'ChromaDB', color: '#FF6B6B' },
    { name: 'LangChain', color: '#3ECF8E' },
    { name: 'GPT-4', color: '#AB68FF' },
    { name: 'Firebase', color: '#FFCA28' },
    { name: 'TypeScript', color: '#3178C6' },
    { name: 'Tailwind', color: '#38BDF8' },
  ]

  return (
    <div className="min-h-screen bg-dark overflow-x-hidden">
      {/* Floating background elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <FloatingIcon icon={DollarSign} delay={0} x="10%" y="20%" size={32} />
        <FloatingIcon icon={TrendingUp} delay={1} x="85%" y="15%" size={28} />
        <FloatingIcon icon={PieChart} delay={2} x="75%" y="60%" size={36} />
        <FloatingIcon icon={Activity} delay={0.5} x="15%" y="70%" size={30} />
        <FloatingIcon icon={BarChart3} delay={1.5} x="90%" y="40%" size={26} />
        <FloatingIcon icon={FileText} delay={3} x="5%" y="45%" size={28} />
        <FloatingIcon icon={BookOpen} delay={2.5} x="50%" y="80%" size={24} />
        <FloatingIcon icon={DollarSign} delay={4} x="60%" y="25%" size={20} />
        
        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-secondary/5 rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
      </div>

      {/* Navigation */}
      <motion.nav 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between glass px-6 py-3 rounded-2xl">
          <h1 className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            FinRAG
          </h1>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/login')}
              className="text-gray-300 hover:text-white transition-colors px-4 py-2 text-sm font-medium"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('/signup')}
              className="btn-primary text-sm !py-2 !px-5"
            >
              Get Started
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <motion.section 
        ref={heroRef}
        style={{ opacity: heroOpacity, scale: heroScale }}
        className="relative min-h-screen flex items-center justify-center px-6 pt-24"
      >
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-8"
          >
            <Sparkles size={14} className="text-primary" />
            <span className="text-sm text-gray-300">AI-Powered Financial Document Analysis</span>
          </motion.div>

          {/* Main heading */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-5xl md:text-7xl font-bold leading-tight mb-6"
          >
            <span className="text-white">Understand </span>
            <span className="bg-gradient-primary bg-clip-text text-transparent">Financial</span>
            <br />
            <span className="text-white">Documents with </span>
            <span className="bg-gradient-primary bg-clip-text text-transparent">AI</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Upload annual reports, balance sheets, and filings. Ask questions in plain English. 
            Get accurate, cited answers grounded in your documents — not hallucinations.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <button
              onClick={() => navigate('/signup')}
              className="btn-primary text-base !py-3.5 !px-8 flex items-center gap-2 group"
            >
              Start Analyzing
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
              }}
              className="btn-secondary text-base !py-3.5 !px-8 flex items-center gap-2"
            >
              See Features
              <ChevronRight size={18} />
            </button>
          </motion.div>

          {/* Hero visual - mock chat */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.0 }}
            className="mt-16 glass p-6 rounded-2xl max-w-2xl mx-auto text-left"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
              <span className="text-xs text-gray-500 ml-2 font-mono">FinRAG — Tesla_10K_2024.pdf</span>
            </div>
            
            <div className="space-y-3">
              <div className="message-user max-w-[80%] ml-auto text-sm">
                What was Tesla's revenue growth in 2024 compared to 2023?
              </div>
              <div className="message-ai max-w-[90%] text-sm">
                <p className="mb-2">Based on the 10-K filing, Tesla reported <strong>$97.7B in revenue</strong> for FY2024, representing a <strong>12.3% increase</strong> from $87.0B in FY2023. 📈</p>
                <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                  <FileText size={10} /> Source: Page 42, Financial Statements
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.section>

      {/* Stats Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="glass rounded-2xl p-10 grid grid-cols-2 md:grid-cols-4 gap-8">
            <AnimatedCounter value={50} suffix="+" label="Document Types Supported" />
            <AnimatedCounter value={99} suffix="%" label="Citation Accuracy" />
            <AnimatedCounter value={30} suffix="+" label="Financial Metrics" />
            <AnimatedCounter value={3} suffix="s" label="Average Response Time" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-primary text-sm font-semibold tracking-wider uppercase">Features</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Everything You Need for Financial Analysis
            </h2>
            <p className="text-gray-400 mt-4 max-w-xl mx-auto">
              From document ingestion to AI-powered insights — a complete toolkit designed for retail investors.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <FeatureCard key={feature.title} {...feature} delay={i * 0.1} />
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <span className="text-primary text-sm font-semibold tracking-wider uppercase">How It Works</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              RAG Pipeline — From PDF to Insights
            </h2>
            <p className="text-gray-400 mt-4 max-w-xl mx-auto">
              Our Retrieval-Augmented Generation pipeline ensures every answer is grounded in your actual documents.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-12 items-start">
            {/* Left: Pipeline steps */}
            <div className="space-y-2">
              {pipeline.map((step, i) => (
                <PipelineStep
                  key={step.title}
                  step={i + 1}
                  {...step}
                  isLast={i === pipeline.length - 1}
                  delay={i * 0.15}
                />
              ))}
            </div>

            {/* Right: Visual diagram */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="glass p-6 rounded-2xl"
            >
              <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Activity size={18} className="text-primary" />
                Why RAG Beats Plain LLM
              </h4>
              
              <div className="space-y-4">
                <div className="glass p-4 rounded-xl border border-red-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-red-500" />
                    <span className="text-red-400 text-sm font-medium">LLM Only</span>
                  </div>
                  <p className="text-gray-400 text-xs leading-relaxed">
                    "Tesla's revenue was approximately $80 billion in 2024..."
                  </p>
                  <p className="text-red-400/70 text-xs mt-1">❌ No source • Potentially hallucinated</p>
                </div>

                <div className="glass p-4 rounded-xl border border-green-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-green-400 text-sm font-medium">RAG (FinRAG)</span>
                  </div>
                  <p className="text-gray-400 text-xs leading-relaxed">
                    "Tesla reported $97.7B in revenue for FY2024, a 12.3% increase from FY2023..."
                  </p>
                  <p className="text-green-400/70 text-xs mt-1">✅ Page 42, Financial Statements • Verified</p>
                </div>
              </div>

              <div className="mt-4 p-3 bg-primary/5 rounded-xl border border-primary/10">
                <p className="text-xs text-gray-300 flex items-center gap-2">
                  <Shield size={14} className="text-primary flex-shrink-0" />
                  RAG reduces hallucination by grounding answers in the actual document context.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12"
          >
            <span className="text-primary text-sm font-semibold tracking-wider uppercase">Built With</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-3">
              Modern Tech Stack
            </h2>
          </motion.div>

          <div className="flex flex-wrap justify-center gap-4">
            {techStack.map((tech, i) => (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                whileHover={{ scale: 1.1, y: -4 }}
                className="glass px-5 py-3 rounded-xl flex items-center gap-2 cursor-default"
              >
                <div 
                  className="w-2.5 h-2.5 rounded-full" 
                  style={{ backgroundColor: tech.color }}
                />
                <span className="text-sm text-gray-300 font-medium">{tech.name}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass p-12 rounded-3xl relative overflow-hidden"
          >
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-secondary/10" />
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Ready to Analyze Your Documents?
              </h2>
              <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                Upload your first financial document and start getting AI-powered insights in seconds. 
                No complicated setup needed.
              </p>
              <button
                onClick={() => navigate('/signup')}
                className="btn-primary text-base !py-4 !px-10 flex items-center gap-2 mx-auto group"
              >
                Get Started — It's Free
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold bg-gradient-primary bg-clip-text text-transparent">FinRAG</h2>
            <span className="text-gray-500 text-sm">•</span>
            <span className="text-gray-500 text-sm">RAG-Powered Financial Analysis</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span>Built with FastAPI + React + ChromaDB</span>
            <span>© {new Date().getFullYear()}</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
