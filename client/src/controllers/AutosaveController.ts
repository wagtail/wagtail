import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';

export enum ErrorCode {
  BLOCKED_BY_HOOK = 'blocked_by_hook',
  INTERNAL_ERROR = 'internal_error',
  INVALID_REVISION = 'invalid_revision',
  LOCKED = 'locked',
  VALIDATION_ERROR = 'validation_error',
}

export interface AutosaveErrorResponse {
  success: false;
  errorCode: ErrorCode;
  errorMessage: string;
}

export interface AutosaveSuccessResponse {
  success: true;
  pk: number | string;
  revision_id?: number;
  url?: string;
}

export type AutosaveResponse = AutosaveSuccessResponse | AutosaveErrorResponse;

export class AutosaveController extends Controller<HTMLFormElement> {
  static targets = ['overwriteRevisionId'];

  declare hasOverwriteRevisionIdTarget: boolean;
  declare readonly overwriteRevisionIdTarget: HTMLInputElement;

  async submit(event?: Event) {
    const formData = new FormData(this.element);
    const saveEvent = this.dispatch('save', {
      cancelable: true,
      detail: { formData, trigger: event },
    });
    if (saveEvent.defaultPrevented) return;

    const requestInit: RequestInit = {
      method: this.element.method,
      body: formData,
      headers: {
        Accept: 'application/json',
        [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      },
    };

    let response: AutosaveResponse | null = null;

    try {
      response = await fetch(
        this.element.action,
        requestInit,
      ).then<AutosaveResponse>((res) => res.json());

      // If we reach here, response must be JSON, but can be of any shape
      if (!response.success) {
        throw new Error(response!.errorMessage || 'Unknown error');
      }

      if (this.hasOverwriteRevisionIdTarget && response?.revision_id) {
        this.overwriteRevisionIdTarget.value = `${response.revision_id}`;
      }
      if (response.url) {
        this.element.action = response.url;
      }

      this.dispatch('success', {
        cancelable: false,
        detail: { response, data: response, trigger: event },
      });
    } catch (error) {
      // Error could be from fetch failing, non-JSON response, or success: false
      this.dispatch('error', {
        cancelable: false,
        detail: {
          response,
          error,
          trigger: event,
          // Used for showing the unsaved changes message again
          type: 'edits',
        },
      });
    }
  }
}
