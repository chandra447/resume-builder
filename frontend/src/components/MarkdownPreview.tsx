import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Paper, Box } from '@mui/material';
import { styled } from '@mui/material/styles';

const PreviewContainer = styled(Paper)(({ theme }) => ({
    height: '100%',
    overflow: 'auto',
    padding: theme.spacing(3),
    backgroundColor: theme.palette.background.paper,
    '& h1': {
        color: theme.palette.primary.main,
        marginBottom: theme.spacing(2),
    },
    '& h2': {
        color: theme.palette.text.primary,
        marginBottom: theme.spacing(1.5),
    },
    '& h3': {
        color: theme.palette.text.secondary,
        marginBottom: theme.spacing(1),
    },
    '& p': {
        marginBottom: theme.spacing(1.5),
        lineHeight: 1.6,
    },
    '& ul, & ol': {
        marginBottom: theme.spacing(1.5),
        paddingLeft: theme.spacing(2),
    },
    '& li': {
        marginBottom: theme.spacing(0.5),
    },
    '& table': {
        width: '100%',
        borderCollapse: 'collapse',
        marginBottom: theme.spacing(2),
    },
    '& th, & td': {
        border: `1px solid ${theme.palette.divider}`,
        padding: theme.spacing(1),
        textAlign: 'left',
    },
    '& th': {
        backgroundColor: theme.palette.grey[100],
    },
    '& code': {
        backgroundColor: theme.palette.grey[100],
        padding: theme.spacing(0.25, 0.5),
        borderRadius: theme.shape.borderRadius,
        fontSize: '0.875em',
    },
    '& pre': {
        margin: theme.spacing(2, 0),
    },
}));

interface MarkdownPreviewProps {
    content: string;
    markdown?: string; // Add optional markdown prop for backward compatibility
}

export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ content, markdown }) => {
    // Use either content or markdown prop, with content taking precedence
    const markdownContent = content || markdown || '';
    
    return (
        <PreviewContainer elevation={0}>
            <ReactMarkdown
                components={{
                    // @ts-ignore - Ignoring TypeScript errors for code component
                    code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                            <SyntaxHighlighter
                                style={tomorrow}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                            >
                                {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                        ) : (
                            <code className={className} {...props}>
                                {children}
                            </code>
                        );
                    },
                }}
            >
                {markdownContent}
            </ReactMarkdown>
        </PreviewContainer>
    );
}; 