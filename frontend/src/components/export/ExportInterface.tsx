// "use client"

// import React, { useState } from 'react';
// import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
// import { Download, FileText, Eye, CheckCircle, AlertCircle } from 'lucide-react';

// const ExportInterface = () => {
//   const [selectedFormat, setSelectedFormat] = useState('geojson');
//   const [showMetadata, setShowMetadata] = useState(false);

//   const formats = [
//     { id: 'shapefile', name: 'Shapefile (.shp)', description: 'Standard GIS format with embedded metadata' },
//     { id: 'geojson', name: 'GeoJSON', description: 'Web-friendly format with full analysis history' },
//     { id: 'geopackage', name: 'GeoPackage (.gpkg)', description: 'OGC standard format' },
//     { id: 'report', name: 'Detailed Report (.pdf)', description: 'Complete analysis documentation' }
//   ];

//   return (
//     <Card className="w-full max-w-4xl">
//       <CardHeader>
//         <CardTitle className="flex items-center gap-2">
//           <Download className="h-5 w-5" />
//           Export Analysis Results
//         </CardTitle>
//       </CardHeader>
//       <CardContent>
//         <div className="space-y-4">
//           {/* Format Selection */}
//           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
//             {formats.map((format) => (
//               <div
//                 key={format.id}
//                 className={`p-4 border rounded-lg cursor-pointer ${
//                   selectedFormat === format.id ? 'border-blue-500 bg-blue-50' : ''
//                 }`}
//                 onClick={() => setSelectedFormat(format.id)}
//               >
//                 <div className="flex items-center gap-2">
//                   <FileText className="h-4 w-4" />
//                   <h3 className="font-medium">{format.name}</h3>
//                 </div>
//                 <p className="text-sm text-gray-600 mt-1">{format.description}</p>
//               </div>
//             ))}
//           </div>

//           {/* Verification Info */}
//           <div className="bg-gray-50 p-4 rounded-lg">
//             <div className="flex items-center gap-2 mb-2">
//               <CheckCircle className="h-4 w-4 text-green-500" />
//               <h3 className="font-medium">Verification Data Included</h3>
//             </div>
//             <div className="space-y-2 text-sm">
//               <div className="flex items-center gap-2">
//                 <Eye className="h-4 w-4" />
//                 <span>Full analysis history and data sources</span>
//               </div>
//               <div className="flex items-center gap-2">
//                 <AlertCircle className="h-4 w-4" />
//                 <span>Confidence scores and uncertainty ranges</span>
//               </div>
//             </div>
//           </div>

//           {/* Export Button */}
//           <button className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 flex items-center justify-center gap-2">
//             <Download className="h-4 w-4" />
//             Export Analysis
//           </button>
//         </div>
//       </CardContent>
//     </Card>
//   );
// };

// export default ExportInterface;