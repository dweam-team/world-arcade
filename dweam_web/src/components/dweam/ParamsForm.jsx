import Form from '@rjsf/bootstrap-4';
import validator from '@rjsf/validator-ajv8';
import { log } from 'node_modules/astro/dist/core/logger/core';
import { useEffect, useState } from 'react';

function ParamsForm({ schema, uiSchema, gameType, gameId }) {
  const [isClient, setIsClient] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsClient(true);
    setIsDark(document.documentElement.classList.contains('dark'));

    // Add Bootstrap CSS
    const bootstrapCSS = document.createElement('link');
    bootstrapCSS.href = 'https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css';
    bootstrapCSS.rel = 'stylesheet';
    document.head.appendChild(bootstrapCSS);

    // Function to update theme
    const updateTheme = () => {
      const isDarkMode = document.documentElement.classList.contains('dark');
      setIsDark(isDarkMode);
      
      // Remove old dark theme if it exists
      const oldDarkTheme = document.head.querySelector('link[data-theme="dark"]');
      if (oldDarkTheme) {
        document.head.removeChild(oldDarkTheme);
      }

      // Add dark theme if needed
      if (isDarkMode) {
        const darkThemeCSS = document.createElement('link');
        darkThemeCSS.href = 'https://cdn.jsdelivr.net/npm/@forevolve/bootstrap-dark@1.0.0/dist/css/bootstrap-dark.min.css';
        darkThemeCSS.rel = 'stylesheet';
        darkThemeCSS.setAttribute('data-theme', 'dark');
        document.head.appendChild(darkThemeCSS);
      }
    };

    // Initial theme setup
    updateTheme();

    // Watch for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          updateTheme();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    // Listen for game session ready event
    const handleSessionReady = (event) => {
      setSessionId(event.detail.sessionId);
    };

    window.addEventListener('gameSessionReady', handleSessionReady);

    return () => {
      window.removeEventListener('gameSessionReady', handleSessionReady);
      observer.disconnect();
      document.head.removeChild(bootstrapCSS);
      const darkTheme = document.head.querySelector('link[data-theme="dark"]');
      if (darkTheme) {
        document.head.removeChild(darkTheme);
      }
    };
  }, []);

  if (!isClient) {
    return null;
  }

  return (
    <>
      <style>
        {`
          #root__title, 
          #root__description {
            display: none;
          }
        `}
      </style>
      <Form
        schema={schema}
        uiSchema={uiSchema}
        validator={validator}
        disabled={!sessionId}
        onSubmit={async ({ formData }, originalEvent) => {
          originalEvent.preventDefault();
          if (!sessionId) return;

          try {
            const response = await fetch(`/params/${sessionId}`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                params: formData
              }),
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Parameters updated successfully');
          } catch (error) {
            console.error('Error updating parameters:', error);
          }
        }}
      />
    </>
  );
}

export default ParamsForm; 