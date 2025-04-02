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
} from '@mui/material';
import { Close as CloseIcon, Upload as UploadIcon } from '@mui/icons-material';

interface UploadDialogProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (file: File | null, jobUrl: string) => void;
}

export const UploadDialog: React.FC<UploadDialogProps> = ({
    open,
    onClose,
    onSubmit,
}) => {
    const [file, setFile] = useState<File | null>(null);
    const [jobUrl, setJobUrl] = useState('');
    const [error, setError] = useState('');

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

    const handleSubmit = () => {
        if (!file && !jobUrl) {
            setError('Please upload a resume or provide a job URL');
            return;
        }
        onSubmit(file, jobUrl);
        onClose();
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

                    <Typography variant="subtitle1" gutterBottom>
                        Job Posting URL
                    </Typography>
                    <TextField
                        fullWidth
                        placeholder="https://example.com/job-posting"
                        value={jobUrl}
                        onChange={(e) => setJobUrl(e.target.value)}
                        error={!!error && !file}
                        helperText={error}
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} color="inherit">
                    Cancel
                </Button>
                <Button onClick={handleSubmit} variant="contained" color="primary">
                    Start Tailoring
                </Button>
            </DialogActions>
        </Dialog>
    );
}; 