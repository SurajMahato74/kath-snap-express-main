import React, { useState, useEffect } from 'react';
import { CheckCircle } from 'lucide-react';

// Add global styles for mobile background
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      min-height: 100vh;
      width: 100%;
      overflow-x: hidden;
      overflow-y: auto;
      position: relative;
      background: linear-gradient(135deg, #ffffff 0%, #f7f3f0 25%, #ede4d8 75%, #856043 100%);
      touch-action: pan-y;
    }
    #root, .h-screen {
      min-height: 100vh;
      width: 100%;
      background: linear-gradient(135deg, #ffffff 0%, #f7f3f0 25%, #ede4d8 75%, #856043 100%);
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
    }
    @media (max-width: 1024px) {
      html, body, #root, .h-screen {
        background: linear-gradient(135deg, #ffffff 0%, #f7f3f0 25%, #ede4d8 75%, #856043 100%);
        min-height: 100vh;
        overflow-x: hidden;
      }
    }
  `;
  document.head.appendChild(style);
}

function App() {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  });

  const frames = [
    { image: '/img/screen.jpeg', id: 0 },
    { image: '/img/screen_B.jpeg', id: 1 },
    { image: '/img/search.jpeg', id: 2 },
    { image: '/img/setting.jpeg', id: 3 },
  ];

  // Set launch date (30 days from now)
  const launchDate = new Date();
  launchDate.setDate(launchDate.getDate() + 30);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date().getTime();
      const distance = launchDate.getTime() - now;

      if (distance > 0) {
        setTimeLeft({
          days: Math.floor(distance / (1000 * 60 * 60 * 24)),
          hours: Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
          minutes: Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)),
          seconds: Math.floor((distance % (1000 * 60)) / 1000),
        });
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const frameTimer = setInterval(() => {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentFrame((prev) => (prev + 1) % frames.length);
        setTimeout(() => {
          setIsTransitioning(false);
        }, 100);
      }, 1000);
    }, 6000);

    return () => clearInterval(frameTimer);
  }, [frames.length]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitted(true);
    setEmail('');
    setTimeout(() => setIsSubmitted(false), 3000);
  };

  return (
    <div
      className="min-h-screen w-full flex flex-col relative"
      style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #f7f3f0 25%, #ede4d8 75%, #856043 100%)',
      }}
    >
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row items-center justify-between px-4 sm:px-6 md:px-8 pt-1 sm:pt-3 z-20">
        {/* Logo */}
        <div className="mb-2 sm:mb-0">
          <img
            src="/img/logo_eg.png"
            alt="Logo"
            className="h-12 sm:h-16 md:h-18 lg:h-16 w-auto drop-shadow-md"
          />
        </div>

        {/* Social Icons */}
        <div className="flex space-x-4">
          <a
            href="https://www.facebook.com/share/1GhqG3BLZn/"
            className="cursor-pointer"
            style={{ color: 'black', opacity: 1 }}
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v4.8c4.56-.93 8-4.96 8-9.8z"/>
            </svg>
          </a>
          <a
            href="https://wa.me/9768382318"
            className="cursor-pointer"
            style={{ color: 'black', opacity: 1 }}
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.465 3.488"/>
            </svg>
          </a>
          <a
            href="https://www.instagram.com/ezeyway?utm_source=qr&igsh=bHQyeXN5cDB2NXN5"
            className="cursor-pointer"
            style={{ color: 'black', opacity: 1 }}
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg
              className="w-6 h-6"
              fill="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M7.75 2h8.5A5.75 5.75 0 0 1 22 7.75v8.5A5.75 5.75 0 0 1 16.25 22h-8.5A5.75 5.75 0 0 1 2 16.25v-8.5A5.75 5.75 0 0 1 7.75 2zm0 1.5A4.25 4.25 0 0 0 3.5 7.75v8.5A4.25 4.25 0 0 0 7.75 20.5h8.5a4.25 4.25 0 0 0 4.25-4.25v-8.5A4.25 4.25 0 0 0 16.25 3.5h-8.5zm4.25 3a5.25 5.25 0 1 1 0 10.5 5.25 5.25 0 0 1 0-10.5zm0 1.5a3.75 3.75 0 1 0 0 7.5 3.75 3.75 0 0 0 0-7.5zm5.5-.75a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0z"/>
            </svg>
          </a>

        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10 flex-1 px-4 sm:px-6 lg:px-8 flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-center max-w-7xl mx-auto w-full min-h-full">
          {/* Left Column - Text Content */}
          <div className="text-center lg:text-left lg:ml-24 -mt-8 lg:mt-0">
            {/* Coming Soon Badge */}
            <div
              className="inline-block text-white px-4 py-2 rounded-full text-sm font-medium mb-3"
              style={{ backgroundColor: '#856043' }}
            >
              Coming Soon
            </div>

            {/* Main Heading */}
            <h1
              className="text-2xl sm:text-4xl md:text-5xl font-bold mb-1 leading-tight"
              style={{ color: '#856043' }}
            >
              Get Notified
            </h1>
            <h2 className="text-2xl sm:text-4xl md:text-5xl font-bold text-black mb-3 leading-tight">
              When we Launch
            </h2>

            {/* Countdown Timer */}
            <div className="mb-3">
              <div className="flex justify-center lg:justify-start space-x-2 sm:space-x-3">
                {Object.entries(timeLeft).map(([unit, value]) => (
                  <div key={unit} className="text-center">
                    <div className="relative w-10 h-12 sm:w-16 sm:h-18">
                      <div
                        className="w-full h-full rounded-lg shadow-lg flex flex-col items-center justify-center text-white px-1"
                        style={{
                          background: 'linear-gradient(145deg, #856043, #6b4d36)',
                        }}
                      >
                        <div className="text-sm sm:text-xl font-bold leading-none">{String(value).padStart(2, '0')}</div>
                        <div className="text-xs opacity-80 mt-1">{unit}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Email Form */}
            {!isSubmitted ? (
              <form onSubmit={handleSubmit} className="max-w-md mx-auto lg:mx-0">
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email address"
                    className="w-full px-4 sm:px-6 py-3 sm:py-4 pr-24 sm:pr-32 rounded-full border-2 bg-transparent focus:outline-none transition-colors text-sm sm:text-base"
                    style={{ borderColor: 'black', color: '#856043' }}
                    onFocus={(e) => (e.target.style.borderColor = 'black')}
                    onBlur={(e) => (e.target.style.borderColor = 'black')}
                    required
                  />
                  <button
                    type="submit"
                    className="absolute right-1 sm:right-2 top-1 bottom-1 text-white px-4 sm:px-6 rounded-full transition-colors font-medium text-xs sm:text-sm"
                    style={{ backgroundColor: 'black' }}
                    onMouseEnter={(e) => (e.target.style.backgroundColor = '#856043')}
                    onMouseLeave={(e) => (e.target.style.backgroundColor = 'black')}
                  >
                    Notify Me
                  </button>
                </div>
              </form>
            ) : (
              <div className="flex items-center justify-center lg:justify-start space-x-2 text-green-600">
                <CheckCircle className="w-6 h-6" />
                <span className="text-lg font-medium">Thanks! You'll be the first to know.</span>
              </div>
            )}
          </div>

          {/* Right Column - iPhone Frames */}
          <div className="flex justify-center items-center overflow-hidden lg:mr-24 mt-6 lg:mt-0">
            <div className="relative w-32 h-[280px] sm:w-36 sm:h-[310px] md:w-40 md:h-[350px] lg:w-48 lg:h-[420px] mx-auto flex-shrink-0">
              {frames.map((frame, index) => {
                let scale = '0';
                let opacity = 0;

                if (index === currentFrame && !isTransitioning) {
                  scale = '1';
                  opacity = 1;
                }

                return (
                  <div
                    key={frame.id}
                    className="absolute inset-0 w-full h-full rounded-[2.5rem] p-1 bg-black"
                    style={{
                      transform: `scale(${scale})`,
                      opacity: opacity,
                      transition: 'all 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                      boxShadow:
                        index === currentFrame && !isTransitioning
                          ? '0 25px 50px -12px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(0, 0, 0, 0.1)'
                          : 'none',
                    }}
                  >
                    <div className="w-full h-full rounded-[2rem] overflow-hidden relative bg-black">
                      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-16 h-4 sm:w-18 sm:h-5 md:w-20 md:h-6 lg:w-24 lg:h-7 bg-black rounded-b-2xl z-20"></div>
                      <div
                        className="w-full h-full rounded-[2rem]"
                        style={{
                          backgroundImage: `url("${frame.image}")`,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          backgroundRepeat: 'no-repeat',
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        className="absolute bottom-4 left-4 sm:bottom-6 sm:left-6 text-sm space-x-4 pb-4 sm:pb-6"
        style={{ color: 'black' }}
      >
        <a
          href="#"
          className="cursor-pointer"
          style={{ opacity: 0.8 }}
          onMouseEnter={(e) => (e.target.style.opacity = '1')}
          onMouseLeave={(e) => (e.target.style.opacity = '0.8')}
        >
          Privacy Policy
        </a>
        <a
          href="#"
          className="cursor-pointer"
          style={{ opacity: 0.8 }}
          onMouseEnter={(e) => (e.target.style.opacity = '1')}
          onMouseLeave={(e) => (e.target.style.opacity = '0.8')}
        >
          Download
        </a>
      </div>
    </div>
  );
}

export default App;