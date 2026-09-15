import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

interface LessonRendererProps {
  contentHtml: string;
}

/** Dars kontentini (HTML+Markdown+KaTeX formulalar+jadvallar) chizadi.
 * Backend kontentni allaqachon sanitizatsiya qilib beradi (app/services/sanitize.py). */
export function LessonRenderer({ contentHtml }: LessonRendererProps) {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-img:rounded-xl">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
      >
        {contentHtml}
      </ReactMarkdown>
    </div>
  );
}
