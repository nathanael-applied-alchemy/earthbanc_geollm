// src/components/export/ExportFormatSelector.tsx
'use client'

import React from 'react';
import { FileText } from 'lucide-react';

interface Format {
  id: string;
  name: string;
  description: string;
}

interface ExportFormatSelectorProps {
  selectedFormat: string;
  onFormatChange: (format: string) => void;
}

export function ExportFormatSelector({ selectedFormat, onFormatChange }: ExportFormatSelectorProps) {
  const formats: Format[] = [
    { id: 'shapefile', name: 'Shapefile (.shp)', description: 'Standard GIS format with embedded metadata' },
    { id: 'geojson', name: 'GeoJSON', description: 'Web-friendly format with full analysis history' },
    { id: 'geopackage', name: 'GeoPackage (.gpkg)', description: 'OGC standard format' },
    { id: 'report', name: 'Detailed Report (.pdf)', description: 'Complete analysis documentation' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {formats.map((format) => (
        <div
          key={format.id}
          className={`p-4 border rounded-lg cursor-pointer ${
            selectedFormat === format.id ? 'border-blue-500 bg-blue-50' : ''
          }`}
          onClick={() => onFormatChange(format.id)}
        >
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <h3 className="font-medium">{format.name}</h3>
          </div>
          <p className="text-sm text-gray-600 mt-1">{format.description}</p>
        </div>
      ))}
    </div>
  );
}
