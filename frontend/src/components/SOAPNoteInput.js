import React, { useState, useCallback } from 'react';
import { FaUser, FaCalendar, FaUserMd, FaNotesMedical, FaFileUpload, FaSpinner } from 'react-icons/fa';
import { useDropzone } from 'react-dropzone';
import { analyzeSOAPNote } from '../services/gptService';

const SOAPNoteInput = ({ onSubmit }) => {
  const [soapNote, setSOAPNote] = useState({
    patient_name: '',
    age: '',
    date: new Date().toISOString().split('T')[0],
    provider: '',
    visit_type: '',
    vital_signs: {
      blood_pressure: '',
      heart_rate: '',
      temperature: '',
      respiratory_rate: '',
      oxygen_saturation: ''
    },
    subjective: '',
    objective: '',
    assessment: '',
    plan: ''
  });

  const [inputMode, setInputMode] = useState('form'); // 'form', 'paste', or 'upload'
  const [pastedText, setPastedText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      setAnalyzing(true);
      try {
        const result = await analyzeSOAPNote(file, 'pdf');
        setSOAPNote(prev => ({
          ...prev,
          ...result
        }));
        setInputMode('form');
      } catch (error) {
        console.error('Error processing PDF:', error);
        alert('Error processing PDF file');
      } finally {
        setAnalyzing(false);
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  });

  const handlePastedTextAnalysis = async () => {
    if (!pastedText.trim()) {
      alert('Please paste some text to analyze');
      return;
    }

    setAnalyzing(true);
    try {
      const result = await analyzeSOAPNote(pastedText, 'text');
      setSOAPNote(prev => ({
        ...prev,
        ...result
      }));
      setInputMode('form');
    } catch (error) {
      console.error('Error analyzing text:', error);
      alert('Error analyzing pasted text');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setSOAPNote(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setSOAPNote(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(soapNote);
  };

  return (
    <div className="space-y-6">
      {/* Input Mode Selection */}
      <div className="flex justify-center space-x-4 mb-6">
        <button
          onClick={() => setInputMode('form')}
          className={`px-4 py-2 rounded-md ${
            inputMode === 'form'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Manual Entry
        </button>
        <button
          onClick={() => setInputMode('paste')}
          className={`px-4 py-2 rounded-md ${
            inputMode === 'paste'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Paste Text
        </button>
        <button
          onClick={() => setInputMode('upload')}
          className={`px-4 py-2 rounded-md ${
            inputMode === 'upload'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Upload PDF
        </button>
      </div>

      {analyzing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl flex items-center space-x-4">
            <FaSpinner className="animate-spin h-6 w-6 text-blue-600" />
            <p className="text-lg">Analyzing document...</p>
          </div>
        </div>
      )}

      {inputMode === 'paste' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Paste SOAP Note Text
          </h3>
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            rows={10}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Paste your SOAP note text here..."
          />
          <button
            onClick={handlePastedTextAnalysis}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            disabled={analyzing}
          >
            Analyze Text
          </button>
        </div>
      )}

      {inputMode === 'upload' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${
              isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
          >
            <input {...getInputProps()} />
            <FaFileUpload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-600">
              {isDragActive
                ? 'Drop the PDF here'
                : 'Drag and drop a PDF file here, or click to select'}
            </p>
            {uploadedFile && (
              <p className="mt-2 text-sm text-gray-500">
                Selected file: {uploadedFile.name}
              </p>
            )}
          </div>
        </div>
      )}

      {inputMode === 'form' && (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Patient Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FaUser className="mr-2" />
              Patient Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Patient Name</label>
                <input
                  type="text"
                  value={soapNote.patient_name}
                  onChange={(e) => handleChange('patient_name', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Age</label>
                <input
                  type="number"
                  value={soapNote.age}
                  onChange={(e) => handleChange('age', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Date</label>
                <input
                  type="date"
                  value={soapNote.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Provider</label>
                <input
                  type="text"
                  value={soapNote.provider}
                  onChange={(e) => handleChange('provider', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Visit Type</label>
                <input
                  type="text"
                  value={soapNote.visit_type}
                  onChange={(e) => handleChange('visit_type', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Vital Signs */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FaNotesMedical className="mr-2" />
              Vital Signs
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Blood Pressure</label>
                <input
                  type="text"
                  placeholder="120/80"
                  value={soapNote.vital_signs.blood_pressure}
                  onChange={(e) => handleChange('vital_signs.blood_pressure', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Heart Rate</label>
                <input
                  type="text"
                  placeholder="bpm"
                  value={soapNote.vital_signs.heart_rate}
                  onChange={(e) => handleChange('vital_signs.heart_rate', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Temperature</label>
                <input
                  type="text"
                  placeholder="°F"
                  value={soapNote.vital_signs.temperature}
                  onChange={(e) => handleChange('vital_signs.temperature', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Respiratory Rate</label>
                <input
                  type="text"
                  placeholder="breaths/min"
                  value={soapNote.vital_signs.respiratory_rate}
                  onChange={(e) => handleChange('vital_signs.respiratory_rate', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">O2 Saturation</label>
                <input
                  type="text"
                  placeholder="%"
                  value={soapNote.vital_signs.oxygen_saturation}
                  onChange={(e) => handleChange('vital_signs.oxygen_saturation', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* SOAP Sections */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">SOAP Note</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Subjective</label>
                <textarea
                  value={soapNote.subjective}
                  onChange={(e) => handleChange('subjective', e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Patient's symptoms, concerns, and history..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Objective</label>
                <textarea
                  value={soapNote.objective}
                  onChange={(e) => handleChange('objective', e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Physical examination findings and test results..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Assessment</label>
                <textarea
                  value={soapNote.assessment}
                  onChange={(e) => handleChange('assessment', e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Diagnoses and clinical impressions..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Plan</label>
                <textarea
                  value={soapNote.plan}
                  onChange={(e) => handleChange('plan', e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="Treatment plan, medications, follow-up..."
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Process SOAP Note
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default SOAPNoteInput; 