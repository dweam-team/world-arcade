import { useStore } from '@nanostores/react';
import { isLoading, loadingMessage, loadingDetail } from '../../stores/gameStore';

export default function LoadingOverlay() {
  const loading = useStore(isLoading);
  const message = useStore(loadingMessage);
  const detail = useStore(loadingDetail);

  console.log('LoadingOverlay render:', { loading, message, detail });

  if (!loading) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-8 max-w-md text-center">
        <div className="w-10 h-10 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
        {message && (
          <div className="text-sm font-mono opacity-75 max-w-md text-center px-4 mb-2">
            {message}
          </div>
        )}
        {detail && (
          <div className="text-xs font-mono opacity-50 max-w-md text-center px-4">
            {detail}
          </div>
        )}
      </div>
    </div>
  );
} 