import React from 'react';
import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';

interface ComboBoxItem {
  label?: string | null;
  description?: string | null;
  // icon?: string | JSX.Element | null;
  blockDefId?: string;
}

export interface ComboBoxPreviewProps {
  item: ComboBoxItem;
  previewLabel: string;
}

export default function ComboBoxPreview({
  item: { label, description, blockDefId },
  previewLabel,
}: ComboBoxPreviewProps) {
  const previewURL = blockDefId
    ? new URL(WAGTAIL_CONFIG.ADMIN_URLS.BLOCK_PREVIEW, window.location.href)
    : undefined;
  previewURL?.searchParams.append('id', blockDefId || '');
  return (
    <div className="w-combobox-preview">
      <iframe
        className="w-combobox-preview__iframe"
        title={previewLabel}
        src={previewURL?.toString()}
      />
      <div className="w-combobox-preview__details">
        <div className="w-combobox-preview__label">{label}</div>
        {description ? (
          <p className="w-combobox-preview__description">{description}</p>
        ) : null}
      </div>
    </div>
  );
}
