import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import { useEffect, useState } from 'react';
import { paramsSchema } from '~/stores/gameStore';
import { useStore } from '@nanostores/react';
import { api } from '~/lib/api';

const CustomInput = (props) => {
  const { id, value, required, disabled, onChange, schema } = props;
  return (
    <input
      id={id}
      className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                 text-white placeholder-gray-500
                 disabled:opacity-50 disabled:cursor-not-allowed"
      value={value || ''}
      required={required}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      type={schema.type === 'number' ? 'number' : 'text'}
    />
  );
};

const CustomCheckbox = (props) => {
  const { id, value, disabled, onChange, label } = props;
  return (
    <div className="flex items-center">
      <input
        id={id}
        type="checkbox"
        className="h-5 w-5 rounded border-gray-700 bg-gray-900/50
                   text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-800
                   disabled:opacity-50 disabled:cursor-not-allowed"
        checked={value || false}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <label htmlFor={id} className="ml-2 text-gray-300">
        {label}
      </label>
    </div>
  );
};

const CustomSelect = (props) => {
  const { id, options, value, required, disabled, onChange } = props;
  return (
    <select
      id={id}
      className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                 text-white
                 disabled:opacity-50 disabled:cursor-not-allowed
                 text-base"
      value={value || ''}
      required={required}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
    >
      {options.enumOptions.map(({ label, value }) => (
        <option key={value} value={value} className="bg-gray-800 text-white py-2">
          {label}
        </option>
      ))}
    </select>
  );
};

const CustomFieldTemplate = (props) => {
  const { id, label, help, required, description, errors, children } = props;
  return (
    <div className="mb-8 pd-4">
      <label htmlFor={id} className="block text-lg text-gray-300 mb-2">
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      {children}
      {description && <p className="text-sm text-gray-600 mt-2">{description}</p>}
      {errors && <div className="text-red-400 text-sm mt-2">{errors}</div>}
      {help && <div className="text-sm text-gray-600 mt-2">{help}</div>}
    </div>
  );
};

const CustomObjectFieldTemplate = (props) => {
  const { title, description, properties } = props;
  return (
    <div>
      {title && <h3 className="text-xl text-gray-200 font-semibold mb-4">{title}</h3>}
      {description && <p className="text-sm text-gray-500 mb-6">{description}</p>}
      <div className="flex flex-col gap-16">
        {properties.map((prop) => prop.content)}
      </div>
    </div>
  );
};

const theme = {
  widgets: {
    TextWidget: CustomInput,
    CheckboxWidget: CustomCheckbox,
    SelectWidget: CustomSelect,
  },
  FieldTemplate: CustomFieldTemplate,
  ObjectFieldTemplate: CustomObjectFieldTemplate,
};

// Create the form with custom theme
Form.defaultProps = {
  ...Form.defaultProps,
  ...theme
};

function ParamsPanelReact({ gameType, gameId }) {
  const [isClient, setIsClient] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isDark, setIsDark] = useState(false);
  const schema = useStore(paramsSchema);

  const hasParameters = () => {
    return schema?.schema?.properties && Object.keys(schema.schema.properties).length > 0;
  };

  useEffect(() => {
    setIsClient(true);
    setIsDark(document.documentElement.classList.contains('dark'));


    // Listen for game session ready event
    const handleSessionReady = async (event) => {
      const sid = event.detail.sessionId;
      setSessionId(sid);

      // Fetch schema when session is ready
      const fullSchema = await api.getParamsSchema(sid);
        
      // Extract UI schema from properties
      const uiSchema = {};
      const schema = { ...fullSchema };  // Clone the schema
      
      if (schema?.properties) {
        for (const [key, prop] of Object.entries(schema.properties)) {
          if (!uiSchema[key]) {
            uiSchema[key] = {};
          }
          // Force descriptions to appear after the field
          uiSchema[key]['ui:description'] = prop.description;
          delete prop.description;
          
          if (prop._ui_schema) {
            uiSchema[key] = {
              ...uiSchema[key],
              ...prop._ui_schema
            };
            delete prop._ui_schema;
          }
        }
      }
      
      paramsSchema.set({ schema, uiSchema });
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

  if (!isClient || !schema || !hasParameters()) {
    return null;
  }

  return (
    <div className="bg-gray-800/80 p-8 rounded-2xl">
      <h2 className="text-2xl font-bold text-gray-200 mb-8">Parameters</h2>
      <div className="w-full">
        <style>
          {`
            #root__title, 
            #root__description {
              display: none;
            }
            #root {
              display: flex;
              flex-direction: column;
              gap: 24px;
            }
            .field-description {
              font-size: 0.875rem;  /* text-sm equivalent */
              color: rgb(75 85 99);  /* text-gray-600 equivalent */
              margin-bottom: 0.25rem;
            }
            :root.dark .field-description {
              color: rgb(156 163 175);  /* text-gray-400 equivalent */
            }
          `}
        </style>
        <Form
          schema={schema.schema}
          uiSchema={schema.uiSchema}
          validator={validator}
          disabled={!sessionId}
          className="flex flex-col gap-6"
          onSubmit={async ({ formData }, originalEvent) => {
            if (!sessionId) return;
            await api.updateParams(sessionId, formData);
          }}
        >
          <button 
            type="submit" 
            className="mt-6 px-8 py-3 bg-blue-600 hover:bg-blue-700 
                     text-white font-semibold rounded-full
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
            disabled={!sessionId}
          >
            Submit
          </button>
        </Form>
      </div>
    </div>
  );
}

export default ParamsPanelReact; 