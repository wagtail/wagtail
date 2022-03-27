import React, { useRef, useEffect } from 'react';

import { renderPattern, simulateLoading } from 'storybook-django';

const getTemplateName = (template?: string, filename?: string): string =>
  template ||
  filename?.replace(/.+\/templates\//, '').replace(/\.stories\..+$/, '.html') ||
  'template-not-found';

type ContextMapping = { [key: string]: any };
type TagsMapping = { [key: string]: any };

interface TemplatePatternProps {
  element?: 'div' | 'span';
  // Path to the template file.
  template?: string;
  // Path to a Storybook `stories` file, which should be placed next to and named the same as the HTML template.
  filename?: string;
  context?: ContextMapping;
  tags?: TagsMapping;
}

const PATTERN_LIBRARY_RENDER_URL = '/pattern-library/api/v1/render-pattern';

/**
 * Retrieves a template pattern’s HTML (or error response) from the server.
 */
export const getTemplatePattern = (
  templateName: string,
  context: ContextMapping,
  tags: TagsMapping,
  callback: (html: string) => void,
) =>
  renderPattern(PATTERN_LIBRARY_RENDER_URL, templateName, context, tags)
    .catch(callback)
    .then((res) => res.text())
    .then(callback);

/**
 * Renders one of our Django templates as if it was a React component.
 * All props are marked as optional, but either template or filename should be provided.
 */
const TemplatePattern = ({
  element = 'div',
  template,
  filename,
  context = {},
  tags = {},
}: TemplatePatternProps) => {
  const ref = useRef(null);

  useEffect(() => {
    const templateName = getTemplateName(template, filename);
    getTemplatePattern(templateName, context, tags, (html) =>
      simulateLoading(ref.current, html),
    );
  });

  return React.createElement(element, { ref });
};

export default TemplatePattern;
