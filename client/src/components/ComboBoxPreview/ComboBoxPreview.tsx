import React from 'react';
import { WAGTAIL_CONFIG } from '../../config/wagtailConfig';

interface ComboBoxItem {
  icon?: JSX.Element | null;
  label?: string | null;
  description?: string | null;
  blockDefId?: string;
}

export interface ComboBoxPreviewProps {
  item: ComboBoxItem;
}

export default function ComboBoxPreview({
  item: { icon, label, description, blockDefId },
}: ComboBoxPreviewProps) {
  const previewURL = blockDefId
    ? new URL(WAGTAIL_CONFIG.ADMIN_URLS.BLOCK_PREVIEW, window.location.href)
    : undefined;
  previewURL?.searchParams.append('id', blockDefId || '');
  return (
    <div className="w-combobox-preview">
      <iframe
        className="w-combobox-preview__iframe"
        title="Preview"
        src={previewURL?.toString()}
      />
      <div className="w-combobox-preview__label">
        <div className="w-combobox-preview__icon">{icon}</div>
        <div className="w-combobox-preview__label-text">{label}</div>
      </div>
      {description ? (
        <p className="w-combobox-preview__description">{description}</p>
      ) : null}
    </div>
  );
}
