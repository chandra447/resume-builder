import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Box,
    Typography,
    IconButton,
    CircularProgress,
    Alert,
} from '@mui/material';
import { Close as CloseIcon, Upload as UploadIcon } from '@mui/icons-material';
import { api } from '../services/api';

interface UploadDialogProps {
    open: boolean;
    onClose: () => void;
    onSuccess: (sessionId: string) => void;
}

export const UploadDialog: React.FC<UploadDialogProps> = ({
    open,
    onClose,
    onSuccess,
}) => {
    const [file, setFile] = useState<File | null>(null);
    const [jobUrl, setJobUrl] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [inputMethod, setInputMethod] = useState<'url' | 'text'>('url');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            const selectedFile = event.target.files[0];
            if (selectedFile.type === 'application/pdf') {
                setFile(selectedFile);
                setError('');
            } else {
                setError('Please upload a PDF file');
            }
        }
    };

    const handleSubmit = async () => {
        // Validate inputs
        if (!file) {
            setError('Please upload a resume PDF');
            return;
        }

        if (inputMethod === 'url' && !jobUrl) {
            setError('Please provide a job posting URL');
            return;
        }

        if (inputMethod === 'text' && !jobDescription) {
            setError('Please provide a job description');
            return;
        }

        setLoading(true);
        setError('');

        try {
            // Create FormData to send file and job details
            const formData = new FormData();
            formData.append('resume_file', file);
            
            if (inputMethod === 'url') {
                formData.append('job_url', jobUrl);
            } else {
                formData.append('job_description', jobDescription);
            }

            // Send to backend
            const response = await api.post('/api/v1/upload-resume-and-job/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            // Handle successful response
            if (response.data && response.data.id) {
                onSuccess(response.data.id);
                // Reset form
                setFile(null);
                setJobUrl('');
                setJobDescription('');
                onClose();
            }
        } catch (err: any) {
            console.error('Error uploading resume and job details:', err);
            setError(err.response?.data?.detail || 'Failed to process your request. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    Upload Resume & Job Details
                    <IconButton onClick={onClose} size="small">
                        <CloseIcon />
                    </IconButton>
                </Box>
            </DialogTitle>
            <DialogContent>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                
                <Box my={2}>
                    <Typography variant="subtitle1" gutterBottom>
                        Upload Resume (PDF)
                    </Typography>
                    <Box
                        border="2px dashed"
                        borderColor="primary.main"
                        borderRadius={2}
                        p={3}
                        textAlign="center"
                        mb={2}
                    >
                        <input
                            accept="application/pdf"
                            style={{ display: 'none' }}
                            id="resume-file"
                            type="file"
                            onChange={handleFileChange}
                        />
                        <label htmlFor="resume-file">
                            <Button
                                variant="outlined"
                                component="span"
                                startIcon={<UploadIcon />}
                            >
                                Choose File
                            </Button>
                        </label>
                        {file && (
                            <Typography variant="body2" mt={1}>
                                Selected: {file.name}
                            </Typography>
                        )}
                    </Box>

                    <Box mb={2}>
                        <Typography variant="subtitle1" gutterBottom>
                            Job Details
                        </Typography>
                        <Box display="flex" gap={1} mb={2}>
                            <Button 
                                variant={inputMethod === 'url' ? "contained" : "outlined"}
                                onClick={() => setInputMethod('url')}
                            >
                                Job URL
                            </Button>
                            <Button 
                                variant={inputMethod === 'text' ? "contained" : "outlined"}
                                onClick={() => setInputMethod('text')}
                            >
                                Job Description
                            </Button>
                        </Box>

                        {inputMethod === 'url' ? (
                            <TextField
                                fullWidth
                                placeholder="https://example.com/job-posting"
                                value={jobUrl}
                                onChange={(e) => setJobUrl(e.target.value)}
                                label="Job Posting URL"
                            />
                        ) : (
                            <TextField
                                fullWidth
                                multiline
                                rows={4}
                                placeholder="Paste the job description here..."
                                value={jobDescription}
                                onChange={(e) => setJobDescription(e.target.value)}
                                label="Job Description"
                            />
                        )}
                    </Box>
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} color="inherit" disabled={loading}>
                    Cancel
                </Button>
                <Button 
                    onClick={handleSubmit} 
                    variant="contained" 
                    color="primary"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    {loading ? 'Processing...' : 'Start Tailoring'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}; 