import Form from '@rjsf/bootstrap-4';
import validator from '@rjsf/validator-ajv8';
import { log } from 'node_modules/astro/dist/core/logger/core';
import { useEffect, useState } from 'react';

function ParamsForm({ schema, gameType, gameId }) {
  const [isClient, setIsClient] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    setIsClient(true);

    // Listen for game session ready event
    const handleSessionReady = (event) => {
      setSessionId(event.detail.sessionId);
    };

    window.addEventListener('gameSessionReady', handleSessionReady);

    return () => {
      window.removeEventListener('gameSessionReady', handleSessionReady);
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
          .form-control {
            background-color: #121212;
            color: #fff;
          }
          .btn.disabled {
            background-color: #343a40;
            color: #6c757d;
          }
        `}
      </style>
      <Form
        schema={schema}
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