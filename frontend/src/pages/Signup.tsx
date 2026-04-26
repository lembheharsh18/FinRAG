import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, Lock, User, Eye, EyeOff, AlertCircle, ArrowRight, Check, Sparkles } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { signUp, signInWithGoogle } = useAuth()

  // Password strength checks
  const hasMinLength = password.length >= 8
  const hasUppercase = /[A-Z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const passwordsMatch = password === confirmPassword && password.length > 0
  const strengthScore = [hasMinLength, hasUppercase, hasNumber].filter(Boolean).length

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    if (!hasMinLength || !hasUppercase || !hasNumber) {
      setError('Please meet all password requirements')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)

    try {
      await signUp(email, password, name)
      navigate('/dashboard')
    } catch (err: any) {
      setError(getErrorMessage(err.code))
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setError('')
    setLoading(true)

    try {
      await signInWithGoogle()
      navigate('/dashboard')
    } catch (err: any) {
      setError(getErrorMessage(err.code))
    } finally {
      setLoading(false)
    }
  }

  const getErrorMessage = (code: string): string => {
    switch (code) {
      case 'auth/email-already-in-use':
        return 'An account with this email already exists'
      case 'auth/invalid-email':
        return 'Invalid email address'
      case 'auth/weak-password':
        return 'Password is too weak'
      case 'auth/popup-closed-by-user':
        return 'Sign-in popup was closed. Please try again'
      case 'auth/popup-blocked':
        return 'Popup was blocked by your browser. Please allow popups'
      default:
        return 'An error occurred. Please try again'
    }
  }

  const PasswordCheck = ({ met, label }: { met: boolean; label: string }) => (
    <motion.div
      className={`flex items-center gap-2 text-sm transition-colors duration-300 ${met ? 'text-green-400' : 'text-gray-500'}`}
      animate={met ? { x: [0, -3, 3, 0] } : {}}
      transition={{ duration: 0.3 }}
    >
      <div className={`w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300 ${met ? 'bg-green-500/20 scale-110' : 'bg-gray-600/20'}`}>
        {met && <Check size={10} />}
      </div>
      {label}
    </motion.div>
  )

  const strengthColors = ['bg-red-500', 'bg-yellow-500', 'bg-green-500']
  const strengthLabels = ['Weak', 'Fair', 'Strong']

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-mesh">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 -left-32 w-[500px] h-[500px] bg-accent/15 rounded-full blur-[120px]"
          animate={{ x: [0, 40, 0], y: [0, -30, 0], scale: [1, 1.1, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute bottom-1/4 -right-32 w-[400px] h-[400px] bg-primary/15 rounded-full blur-[100px]"
          animate={{ x: [0, -30, 0], y: [0, 40, 0], scale: [1, 1.15, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
        />
        {/* Floating particles */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-accent/40 rounded-full"
            style={{ left: `${15 + i * 15}%`, top: `${20 + (i % 3) * 25}%` }}
            animate={{ y: [0, -40, 0], opacity: [0.2, 0.8, 0.2] }}
            transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut', delay: i * 0.5 }}
          />
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-4">
            <Sparkles size={14} className="text-accent" />
            <span className="text-xs text-gray-400 font-medium">Join the future of finance</span>
          </div>
          <h1 className="text-5xl font-bold font-display bg-gradient-to-r from-accent via-primary to-secondary bg-clip-text text-transparent">
            FinRAG
          </h1>
          <p className="text-gray-400 mt-2">Create your account</p>
        </motion.div>

        {/* Glass card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="glass-card-glow"
        >
          <h2 className="text-2xl font-semibold font-display text-white mb-6">Get started</h2>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6 animate-shake"
            >
              <AlertCircle size={18} />
              <span className="text-sm">{error}</span>
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Full name</label>
              <div className="relative group">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" size={18} />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="input-field pl-11"
                  required
                />
              </div>
            </div>

            {/* Email field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Email</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input-field pl-11"
                  required
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Password</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" size={18} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pl-11 pr-11"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              
              {/* Animated strength bar */}
              {password.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-3"
                >
                  <div className="flex gap-1 mb-2">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-colors duration-500 ${
                          i < strengthScore ? strengthColors[strengthScore - 1] : 'bg-gray-700'
                        }`}
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: 1 }}
                        transition={{ duration: 0.3, delay: i * 0.1 }}
                      />
                    ))}
                  </div>
                  <p className={`text-xs mb-2 ${strengthScore === 3 ? 'text-green-400' : strengthScore === 2 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {strengthLabels[strengthScore - 1] || 'Too weak'}
                  </p>
                  <div className="space-y-1">
                    <PasswordCheck met={hasMinLength} label="At least 8 characters" />
                    <PasswordCheck met={hasUppercase} label="One uppercase letter" />
                    <PasswordCheck met={hasNumber} label="One number" />
                  </div>
                </motion.div>
              )}
            </div>

            {/* Confirm Password field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Confirm password</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" size={18} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className={`input-field pl-11 ${confirmPassword && !passwordsMatch ? 'input-error' : ''}`}
                  required
                />
                {passwordsMatch && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 400 }}
                  >
                    <Check className="absolute right-4 top-1/2 -translate-y-1/2 text-green-400" size={18} />
                  </motion.div>
                )}
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-6"
            >
              {loading ? (
                <div className="spinner-branded !w-5 !h-5 !border-2 !border-white/20 !border-t-white" />
              ) : (
                <>
                  Create account
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            <span className="text-gray-500 text-sm">or</span>
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          </div>

          {/* Google sign in */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="btn-google"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.75h3.57c2.08-1.92 3.28-4.74 3.28-8.07z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.75c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.12c-.22-.66-.35-1.36-.35-2.12s.13-1.46.35-2.12V7.04H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.96l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.04l3.66 2.84c.87-2.6 3.3-4.5 6.16-4.5z" />
            </svg>
            Continue with Google
          </button>

          {/* Sign in link */}
          <p className="text-center text-gray-400 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="link font-medium">
              Sign in
            </Link>
          </p>
        </motion.div>
      </motion.div>
    </div>
  )
}
