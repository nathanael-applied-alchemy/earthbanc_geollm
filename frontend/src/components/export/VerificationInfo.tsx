
// src/components/export/VerificationInfo.tsx
'use client'

import React from 'react';
import { CheckCircle, Eye, AlertCircle } from 'lucide-react';

interface VerificationInfoProps {
  metadata?: {
    confidence: number;
    timestamp: string;
    dataSource: string[];
  };
}

export function VerificationInfo({ metadata }: VerificationInfoProps) {
  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle className="h-4 w-4 text-green-500" />
        <h3 className="font-medium">Verification Data Included</h3>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4" />
          <span>Full analysis history and data sources</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span>Confidence scores and uncertainty ranges</span>
        </div>
        {metadata && (
          <div className="mt-4 text-xs text-gray-600">
            <p>Confidence: {metadata.confidence}%</p>
            <p>Last Updated: {new Date(metadata.timestamp).toLocaleString()}</p>
            <p>Data Sources: {metadata.dataSource.join(', ')}</p>
          </div>
        )}
      </div>
    </div>
  );
}
