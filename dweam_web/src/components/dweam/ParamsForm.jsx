import Form from '@rjsf/bootstrap-4';
import validator from '@rjsf/validator-ajv8';
import { useEffect, useState } from 'react';
import { paramsSchema } from '~/stores/gameStore';
import { useStore } from '@nanostores/react';
import { api } from '~/lib/api';
function ParamsForm({ gameType, gameId }) {
  const [isClient, setIsClient] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isDark, setIsDark] = useState(false);
  const schema = useStore(paramsSchema);

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
    const handleSessionReady = async (event) => {
      const sid = event.detail.sessionId;
      setSessionId(sid);

      // Fetch schema when session is ready
      try {
        const response = await api.getParamsSchema(sid);
        if (response.ok) {
          const fullSchema = await response.json();
          
          // Extract UI schema from properties
          const uiSchema = {};
          const schema = { ...fullSchema };  // Clone the schema
          
          if (schema?.properties) {
            for (const [key, prop] of Object.entries(schema.properties)) {
              // UI Schema is stored directly in _ui_schema
              if (prop._ui_schema) {
                uiSchema[key] = prop._ui_schema;
                delete prop._ui_schema;  // Clean up schema
              }
            }
          }
          
          paramsSchema.set({ schema, uiSchema });
        }
      } catch (error) {
        console.error('Error fetching schema:', error);
      }
    };

    window.addEventListener('gameSessionReady', handleSessionReady);
    window.addEventListener('gameSessionEnd', () => setSessionId(null));

    return () => {
      window.removeEventListener('gameSessionReady', handleSessionReady);
      window.removeEventListener('gameSessionEnd', () => setSessionId(null));
      observer.disconnect();
      document.head.removeChild(bootstrapCSS);
      const darkTheme = document.head.querySelector('link[data-theme="dark"]');
      if (darkTheme) {
        document.head.removeChild(darkTheme);
      }
    };
  }, []);

  if (!isClient || !schema) {
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
        schema={schema.schema}
        uiSchema={schema.uiSchema}
        validator={validator}
        disabled={!sessionId}
        onSubmit={async ({ formData }, originalEvent) => {
          originalEvent.preventDefault();
          if (!sessionId) return;

          try {
            const response = await api.getParamsSchema(sid);

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