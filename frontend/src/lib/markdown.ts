/**
 * Markdown to HTML Renderer
 * 
 * A unified, reusable markdown renderer for digest content.
 * Handles headings, bold, italic, bullet lists, numbered lists, and line breaks.
 * 
 * @module lib/markdown
 */

interface RenderOptions {
    /** If true, truncates content for preview display */
    preview?: boolean;
    /** Maximum number of lines to show in preview mode */
    maxLines?: number;
    /** Whether to apply styling classes */
    styled?: boolean;
}

/**
 * Renders markdown content to HTML.
 * 
 * Processes in the correct order to avoid conflicts:
 * 1. Headings (must be at start of line)
 * 2. Bold text (before italic to avoid conflicts with single asterisks)
 * 3. Italic text
 * 4. Bullet lists (wrap consecutive items in <ul>)
 * 5. Numbered lists (wrap consecutive items in <ol>)
 * 6. Paragraphs (double newlines)
 * 7. Line breaks (single newlines not part of lists)
 * 
 * @param content - Raw markdown string
 * @param options - Rendering options
 * @returns HTML string
 */
export function renderDigestMarkdown(
    content: string,
    options: RenderOptions = {}
): string {
    const { preview = false, maxLines = 30, styled = true } = options;

    // Truncate for preview mode
    let processedContent = preview
        ? content.split('\n').slice(0, maxLines).join('\n')
        : content;

    // CSS class definitions based on styled option
    const classes = {
        h1: styled ? 'text-3xl font-bold mb-4 mt-8 text-foreground' : '',
        h2: styled ? 'text-2xl font-semibold mb-3 mt-6 text-foreground' : '',
        h3: styled ? 'text-xl font-medium mb-2 mt-4 text-foreground' : '',
        li: styled ? 'ml-4 text-muted-foreground' : '',
        liDecimal: styled ? 'ml-4 text-muted-foreground list-decimal' : '',
        p: styled ? 'mb-4 leading-relaxed text-muted-foreground' : '',
        ul: styled ? 'list-disc mb-4' : 'list-disc',
        ol: styled ? 'list-decimal mb-4' : 'list-decimal',
    };

    // Helper to add class attribute if class string is not empty
    const cls = (className: string) => (className ? ` class="${className}"` : '');

    // Step 1: Process headings (must be at start of line)
    processedContent = processedContent
        .replace(/^### (.*$)/gim, `<h3${cls(classes.h3)}>$1</h3>`)
        .replace(/^## (.*$)/gim, `<h2${cls(classes.h2)}>$1</h2>`)
        .replace(/^# (.*$)/gim, `<h1${cls(classes.h1)}>$1</h1>`);

    // Step 2: Process bold text (non-greedy to handle multiple bold sections)
    processedContent = processedContent.replace(
        /\*\*(.*?)\*\*/g,
        '<strong>$1</strong>'
    );

    // Step 3: Process italic text (non-greedy, must come after bold)
    processedContent = processedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Step 4: Process bullet lists - wrap consecutive items in <ul>
    processedContent = wrapListItems(
        processedContent,
        /^- (.*)$/gm,
        `<li${cls(classes.li)}>$1</li>`,
        `<ul${cls(classes.ul)}>`,
        '</ul>'
    );

    // Step 5: Process numbered lists - wrap consecutive items in <ol>
    processedContent = wrapListItems(
        processedContent,
        /^\d+\. (.*)$/gm,
        `<li${cls(classes.liDecimal)}>$1</li>`,
        `<ol${cls(classes.ol)}>`,
        '</ol>'
    );

    // Step 6: Process paragraphs (double newlines become paragraph breaks)
    processedContent = processedContent.replace(
        /\n\n/g,
        `</p><p${cls(classes.p)}>`
    );

    // Step 7: Process remaining single newlines as line breaks
    // But not if they're adjacent to block elements
    processedContent = processedContent.replace(
        /\n(?!<\/?(ul|ol|li|h[1-6]|p))/g,
        '<br />'
    );

    // Clean up any empty paragraphs or stray breaks after block elements
    processedContent = processedContent
        .replace(/<br \/>\s*(<\/(ul|ol|h[1-6])>)/g, '$1')
        .replace(/(<(ul|ol|h[1-6])[^>]*>)\s*<br \/>/g, '$1')
        .replace(/<p[^>]*>\s*<\/p>/g, '');

    return processedContent;
}

/**
 * Wraps consecutive matching lines in a container element.
 * This ensures list items are properly wrapped in <ul> or <ol> tags.
 * 
 * @param content - The content to process
 * @param pattern - Regex pattern to match list items
 * @param replacement - Replacement string for each item
 * @param openTag - Opening wrapper tag (e.g., '<ul>')
 * @param closeTag - Closing wrapper tag (e.g., '</ul>')
 * @returns Processed content with wrapped list items
 */
function wrapListItems(
    content: string,
    pattern: RegExp,
    replacement: string,
    openTag: string,
    closeTag: string
): string {
    const lines = content.split('\n');
    const result: string[] = [];
    let inList = false;

    for (const line of lines) {
        const isListItem = pattern.test(line);
        // Reset the regex lastIndex since we're using global flag
        pattern.lastIndex = 0;

        if (isListItem) {
            if (!inList) {
                result.push(openTag);
                inList = true;
            }
            result.push(line.replace(pattern, replacement));
        } else {
            if (inList) {
                result.push(closeTag);
                inList = false;
            }
            result.push(line);
        }
    }

    // Close any open list at the end
    if (inList) {
        result.push(closeTag);
    }

    return result.join('\n');
}

/**
 * Renders markdown for preview display.
 * Convenience wrapper with preview defaults.
 * 
 * @param content - Raw markdown string
 * @param maxLines - Maximum lines to show (default: 30)
 * @returns HTML string suitable for preview
 */
export function renderPreview(content: string, maxLines: number = 30): string {
    return renderDigestMarkdown(content, {
        preview: true,
        maxLines,
        styled: true,
    });
}

/**
 * Renders full markdown content.
 * Convenience wrapper for full content rendering.
 * 
 * @param content - Raw markdown string
 * @returns HTML string
 */
export function renderFullContent(content: string): string {
    return renderDigestMarkdown(content, {
        preview: false,
        styled: true,
    });
}
