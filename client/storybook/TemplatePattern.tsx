import React, { useRef, useEffect } from 'react';

import { renderPattern, simulateLoading } from 'storybook-django';

const getTemplateName = (template?: string, filename?: string) =>
  template ||
  filename?.replace(/.+\/templates\//, '').replace(/\.stories\..+$/, '.html');

interface TemplatePatternProps {
  element?: 'div' | 'span';
  template?: string;
  filename?: string;
  context?: { [key: string]: any };
  tags?: { [key: string]: any };
}

const TemplatePattern = ({
  element = 'div',
  template,
  filename,
  context = {},
  tags = {},
}: TemplatePatternProps) => {
  const ref = useRef(null);
  const templateName = getTemplateName(template, filename);

  useEffect(() => {
    renderPattern(window.PATTERN_LIBRARY_API, templateName, context, tags)
      .catch((err) => simulateLoading(ref.current, err))
      .then((res) => res.text())
      .then((html) => simulateLoading(ref.current, html));
  }, []);

  return React.createElement(element, { ref });
};

export default TemplatePattern;
