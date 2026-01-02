import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { gettext } from '../utils/gettext';

export enum ErrorCode {
  BLOCKED_BY_HOOK = 'blocked_by_hook',
  INTERNAL_ERROR = 'internal_error',
  INVALID_REVISION = 'invalid_revision',
  LOCKED = 'locked',
  VALIDATION_ERROR = 'validation_error',
}

export type AutosaveState = 'idle' | 'saving' | 'saved' | 'paused';

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

export interface AutosaveErrorDetail {
  trigger?: Event;
  response?: AutosaveErrorResponse | null;
  error: any;
  type: ErrorCode;
}

export class AutosaveController extends Controller<
  HTMLFormElement | HTMLDivElement
> {
  static targets = ['overwriteRevisionId'];
  static values = {
    active: { type: Boolean, default: true },
    state: { type: String, default: 'idle' as AutosaveState },
  };

  declare hasOverwriteRevisionIdTarget: boolean;
  declare readonly overwriteRevisionIdTarget: HTMLInputElement;

  declare activeValue: boolean;
  declare stateValue: AutosaveState;

  updateRevisionId(event: CustomEvent<{ revisionId: number }>) {
    const { revisionId } = event.detail;
    if (revisionId && this.hasOverwriteRevisionIdTarget) {
      this.overwriteRevisionIdTarget.value = `${revisionId}`;
    }
  }

  async submit(event?: Event) {
    if (!this.activeValue || !(this.element instanceof HTMLFormElement)) return;
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

      if (response.url) {
        this.element.action = response.url;
      }

      this.dispatch('success', {
        cancelable: false,
        detail: {
          response,
          data: response,
          trigger: event,
          revisionId: response.revision_id,
        },
      });
    } catch (error) {
      // Error could be from fetch failing, non-JSON response, or success: false
      const errorResponse = response as AutosaveErrorResponse | null;
      const type = errorResponse?.errorCode || ErrorCode.VALIDATION_ERROR;

      this.dispatch('error', {
        cancelable: false,
        detail: {
          response,
          error,
          trigger: event,
          // Used for showing the unsaved changes message
          type,
        },
      });
    }
  }

  /**
   * Update the indicator component's state based on events dispatched by the
   * controller from the editor form.
   */
  updateIndicator(event: Event) {
    let content = '';

    switch (event.type) {
      case `${this.identifier}:save`:
        this.stateValue = 'saving';
        // Might be unnecessary?
        content = gettext('Autosave in progress…');
        break;
      case `${this.identifier}:success`:
        this.stateValue = 'saved';
        // TODO: Add timestamp of last save?
        content = gettext('Changes have been autosaved.');
        break;
      case `${this.identifier}:error`:
        this.stateValue = 'paused';
        content =
          (event as CustomEvent<AutosaveErrorDetail>).detail.response
            ?.errorMessage ||
          gettext('Failed to autosave due to an unknown error.');
        break;
      default:
        this.stateValue = 'idle';
    }

    this.element.setAttribute('data-w-tooltip-content-value', content);
  }
}
