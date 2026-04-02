import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Box, Typography } from '@mui/material'

interface Props {
  content: string
  sx?: object
}

export default function MarkdownRenderer({ content, sx }: Props) {
  return (
    <Box
      sx={{
        '& p': { mt: 0, mb: 1, lineHeight: 1.7 },
        '& p:last-child': { mb: 0 },
        '& ul, & ol': { pl: 2.5, mb: 1 },
        '& li': { mb: 0.25 },
        '& h1, & h2, & h3': { mt: 1.5, mb: 0.75, fontWeight: 700 },
        '& blockquote': {
          borderLeft: '3px solid',
          borderColor: 'primary.main',
          pl: 2,
          ml: 0,
          color: 'text.secondary',
        },
        '& table': { borderCollapse: 'collapse', width: '100%', mb: 1 },
        '& th, & td': { border: '1px solid', borderColor: 'divider', px: 1.5, py: 0.75 },
        '& th': { bgcolor: 'action.hover', fontWeight: 600 },
        '& a': { color: 'primary.main' },
        ...sx,
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '')
            const isBlock = !props.inline && match
            return isBlock ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match![1]}
                PreTag="div"
                customStyle={{ borderRadius: 8, fontSize: 13, margin: '8px 0' }}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <Typography
                component="code"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.85em',
                  bgcolor: 'action.hover',
                  px: 0.6,
                  py: 0.2,
                  borderRadius: 1,
                }}
              >
                {children}
              </Typography>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  )
}
